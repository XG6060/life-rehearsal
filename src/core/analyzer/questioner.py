"""苏格拉底式追问器 — 生成个性化的追问，帮助用户深入思考"""

from __future__ import annotations

from typing import Optional

from config.prompts.analyzer import build_questioner_prompt
from src.llm.client import LLMResponse, get_llm_client
from src.models.decision import Decision
from src.models.report import BiasItem, Question
from src.utils.logger import logger
from src.utils.text import safe_json_parse


class Questioner:
    """苏格拉底式追问器"""

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()

    def generate(
        self,
        decision: Decision,
        biases: Optional[list[BiasItem]] = None,
    ) -> tuple[list[Question], LLMResponse]:
        """生成个性化追问

        Args:
            decision: 用户的决策信息
            biases: 已检测到的偏误（可选，用于增强追问的针对性）

        Returns:
            (list[Question], LLMResponse)
        """
        # 构造选项字典
        options_dict = [
            {"label": o.label, "description": o.description}
            for o in decision.options
        ] if decision.options else None

        # 提取偏误名称列表
        bias_names = [b.bias_name_cn for b in (biases or [])]

        # 构建 prompt
        system, messages = build_questioner_prompt(
            title=decision.title,
            context=decision.context,
            options=options_dict,
            biases=bias_names if bias_names else None,
            age_range=getattr(decision, 'age_range', ""),
            occupation=getattr(decision, 'occupation_category', ""),
            city=getattr(decision, 'city_tier', ""),
        )

        # 调用 LLM
        response = self.llm.chat(
            system=system,
            messages=messages,
            use_cache=True,
        )
        if not response.success:
            logger.error(f"Question generation LLM call failed: {response.error}")
            return [], response

        # 解析 JSON
        parsed = safe_json_parse(response.content)
        if not parsed:
            logger.warning(f"Failed to parse questions JSON: {response.content[:200]}")
            return [], response

        # 构建追问列表
        questions = self._parse_questions(parsed)
        return questions, response

    def _parse_questions(self, parsed: dict) -> list[Question]:
        """将 LLM 返回的 JSON 解析为 Question 列表"""
        questions = []
        raw_questions = parsed.get("questions", []) if isinstance(parsed, dict) else parsed if isinstance(parsed, list) else []

        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            try:
                question = Question(
                    question=item.get("question", ""),
                    category=item.get("category", "clarify"),
                    reason=item.get("reason", ""),
                )
                if question.question:
                    questions.append(question)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse question item: {e}")

        return questions
