"""LLM 调用封装 — 支持 DeepSeek / OpenAI 兼容 API

支持多个提供商：
- DeepSeek (default, API地址: https://api.deepseek.com)
- OpenAI (API地址: https://api.openai.com/v1)
- 其他兼容 OpenAI 格式的 API

环境变量配置：
    LLM_API_KEY=sk-xxx                 # API Key
    LLM_BASE_URL=https://api.deepseek.com  # API 地址
    LLM_MODEL=deepseek-chat            # 模型名
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Optional

import yaml
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from src.utils.logger import logger

# Load LLM config
LLM_CONFIG_PATH = settings.project_root / "config" / "llm.yaml"
if LLM_CONFIG_PATH.exists():
    with open(LLM_CONFIG_PATH, encoding="utf-8") as f:
        _llm_config = yaml.safe_load(f)
else:
    _llm_config = {}


# ── Types ──────────────────────────────────────────────────────────────


@dataclass
class LLMResponse:
    """标准化的 LLM 响应"""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cached: bool = False
    error: Optional[str] = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class TokenBudget:
    """Token 预算跟踪"""
    max_per_session: int = _llm_config.get("budget", {}).get("max_tokens_per_session", 50000)
    max_per_day: int = _llm_config.get("budget", {}).get("max_tokens_per_day", 200000)
    used_in_session: int = 0
    used_today: int = 0

    @property
    def session_remaining(self) -> int:
        return self.max_per_session - self.used_in_session

    @property
    def session_exhausted(self) -> bool:
        return self.used_in_session >= self.max_per_session

    def record(self, tokens: int) -> None:
        self.used_in_session += tokens
        self.used_today += tokens

    def warn_if_low(self) -> bool:
        warn_at = _llm_config.get("budget", {}).get("warn_at", 0.8)
        ratio = self.used_in_session / self.max_per_session
        if ratio >= warn_at:
            logger.warning(f"Token budget at {ratio:.0%} — {self.session_remaining} remaining")
            return True
        return False


# ── Cache ──────────────────────────────────────────────────────────────


class LLMCache:
    """简单的内存/文件缓存，避免重复调用"""

    def __init__(self, max_entries: int = 1000):
        self._cache: dict[str, tuple[str, float]] = {}
        self.max_entries = max_entries
        self.ttl = _llm_config.get("cache", {}).get("ttl_seconds", 3600)

    def _make_key(self, system: str, messages: list[dict], model: str) -> str:
        raw = json.dumps({"system": system, "messages": messages, "model": model}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, system: str, messages: list[dict], model: str) -> Optional[str]:
        key = self._make_key(system=system, messages=messages, model=model)
        entry = self._cache.get(key)
        if entry is None:
            return None
        content, ts = entry
        if time.time() - ts > self.ttl:
            del self._cache[key]
            return None
        return content

    def set(self, system: str, messages: list[dict], model: str, content: str) -> None:
        key = self._make_key(system=system, messages=messages, model=model)
        if len(self._cache) >= self.max_entries:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest]
        self._cache[key] = (content, time.time())

    def clear(self) -> None:
        self._cache.clear()


# ── Client ─────────────────────────────────────────────────────────────


class LLMClient:
    """LLM API 客户端 — 支持 DeepSeek / OpenAI 等兼容接口"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # 从 settings 或环境变量读取
        self.api_key = api_key or settings.llm_api_key or ""
        self.base_url = base_url or settings.llm_base_url or "https://api.deepseek.com"
        self.default_model = model or settings.llm_model or "deepseek-chat"

        self.cache = LLMCache()
        self.budget = TokenBudget()
        self._op_input = 0
        self._op_output = 0

        if not self.api_key:
            logger.warning("LLM_API_KEY not set — LLM calls will fail")

        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=60.0,  # 60 秒超时，防止 API 卡死
            )
        return self._client

    @property
    def provider(self) -> str:
        """识别提供商名称"""
        if "deepseek" in self.base_url:
            return "deepseek"
        if "openai" in self.base_url:
            return "openai"
        return "custom"

    # ── Core call ──────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"LLM call failed, retrying #{retry_state.attempt_number}..."
        ),
    )
    def _call_sync(
        self,
        system: str,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> dict:
        model = model or self.default_model
        max_tokens = max_tokens or settings.llm_max_tokens
        temperature = temperature if temperature is not None else settings.llm_temperature

        # 构建 OpenAI 格式的 messages（system 作为第一条消息）
        openai_messages: list[dict] = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(messages)

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=openai_messages,
            **kwargs,
        )

        choice = response.choices[0]
        return {
            "content": choice.message.content or "",
            "model": response.model,
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }

    def chat(
        self,
        system: str,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True,
        **kwargs,
    ) -> LLMResponse:
        """调用 LLM API 并返回标准化响应"""
        start = time.time()
        model = model or self.default_model

        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get(system=system, messages=messages, model=model)
            if cached is not None:
                logger.debug(f"LLM cache hit for {model}")
                return LLMResponse(
                    content=cached,
                    model=model,
                    cached=True,
                )

        # Check budget
        if self.budget.session_exhausted:
            return LLMResponse(
                content="",
                model=model,
                error="Token budget exhausted",
            )

        try:
            result = self._call_sync(
                system=system,
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            logger.error(f"LLM call failed after {elapsed}ms: {e}")
            return LLMResponse(
                content="",
                model=model,
                error="LLM API call failed",  # sanitized - don't leak raw exception details
                latency_ms=elapsed,
            )

        elapsed = int((time.time() - start) * 1000)
        response = LLMResponse(
            content=result["content"],
            model=result["model"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            latency_ms=elapsed,
        )

        # Record budget
        self.budget.record(response.total_tokens)
        self._op_input += response.input_tokens
        self._op_output += response.output_tokens
        self.budget.warn_if_low()

        # Update cache
        if use_cache and response.success:
            self.cache.set(system=system, messages=messages, model=model, content=response.content)

        logger.debug(
            f"LLM call: model={model} "
            f"tokens={response.total_tokens} "
            f"latency={elapsed}ms"
        )
        return response

    def chat_json(
        self,
        system: str,
        messages: list[dict],
        model: Optional[str] = None,
        **kwargs,
    ) -> tuple[Optional[dict], LLMResponse]:
        """调用 LLM 并尝试解析 JSON 响应"""
        response = self.chat(system=system, messages=messages, model=model, **kwargs)
        if not response.success:
            return None, response

        from src.utils.text import safe_json_parse

        parsed = safe_json_parse(response.content)
        return parsed, response

    # ── Convenience ───────────────────────────────────────────────

    def chat_simple(
        self,
        user_message: str,
        system: str = "你是一个有帮助的AI助手。",
        model: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """最简单的单轮对话"""
        return self.chat(
            system=system,
            messages=[{"role": "user", "content": user_message}],
            model=model,
            **kwargs,
        )

    def start_tracking(self) -> None:
        """开始追踪一次操作（分析/模拟）的 token 消耗"""
        self._op_input = 0
        self._op_output = 0

    def stop_tracking(self) -> dict:
        """获取本次操作的 token 消耗并重置"""
        result = {"input_tokens": self._op_input, "output_tokens": self._op_output}
        self._op_input = 0
        self._op_output = 0
        return result

    def get_stats(self) -> dict:
        """获取 LLM 使用统计"""
        return {
            "provider": self.provider,
            "model": self.default_model,
            "cache_size": len(self.cache._cache),
            "session_tokens_used": self.budget.used_in_session,
            "session_tokens_remaining": self.budget.session_remaining,
        }


# ── Singleton ──────────────────────────────────────────────────────────

_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端单例"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
