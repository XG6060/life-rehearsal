"""认知偏误检测器 — 识别用户决策描述中的 6 种认知偏误"""

from __future__ import annotations

from typing import Optional

from config.prompts.analyzer import build_bias_detector_prompt
from src.llm.client import LLMResponse, get_llm_client
from src.models.decision import Decision
from src.models.report import BiasItem, BiasType
from src.utils.logger import logger
from src.utils.text import safe_json_parse

# 偏误类型映射
BIAS_TYPE_MAP: dict[str, BiasType] = {
    "loss_aversion": BiasType.LOSS_AVERSION,
    "confirmation_bias": BiasType.CONFIRMATION_BIAS,
    "over_optimism": BiasType.OVER_OPTIMISM,
    "anchoring": BiasType.ANCHORING,
    "status_quo": BiasType.STATUS_QUO,
    "sunk_cost": BiasType.SUNK_COST,
}


class BiasDetector:
    """认知偏误检测器"""

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()

    def detect(
        self,
        decision: Decision,
        style: str = "",
    ) -> tuple[list[BiasItem], LLMResponse]:
        """检测决策描述中的认知偏误

        Returns:
            (list[BiasItem], LLMResponse) — 偏误列表和原始 LLM 响应
        """
        # 构造选项字典
        options_dict = [
            {"label": o.label, "description": o.description}
            for o in decision.options
        ] if decision.options else None

        # 构建 prompt
        system, messages = build_bias_detector_prompt(
            title=decision.title,
            context=decision.context,
            options=options_dict,
            age_range=getattr(decision, 'age_range', ""),
            occupation=getattr(decision, 'occupation_category', ""),
            city=getattr(decision, 'city_tier', ""),
            style=style,
        )

        # 调用 LLM
        response = self.llm.chat(
            system=system,
            messages=messages,
            use_cache=True,
        )
        if not response.success:
            logger.error(f"Bias detection LLM call failed: {response.error}")
            return [], response

        # 解析 JSON
        parsed = safe_json_parse(response.content)
        if not parsed:
            logger.warning(f"Failed to parse bias detection JSON: {response.content[:200]}")
            return [], response

        # 构建偏误列表
        biases = self._parse_biases(parsed)
        return biases, response

    def detect_from_text(
        self,
        title: str,
        context: str,
        options: Optional[list[dict]] = None,
        age_range: str = "",
        style: str = "",
    ) -> tuple[list[BiasItem], LLMResponse]:
        """直接从文本检测偏误"""
        system, messages = build_bias_detector_prompt(
            title=title,
            context=context,
            options=options,
            age_range=age_range,
            occupation="",
            city="",
            style=style,
        )

        response = self.llm.chat(system=system, messages=messages, use_cache=True)
        if not response.success:
            return [], response

        parsed = safe_json_parse(response.content)
        if not parsed:
            return [], response

        return self._parse_biases(parsed), response

    def _parse_biases(self, parsed: dict) -> list[BiasItem]:
        """将 LLM 返回的 JSON 解析为 BiasItem 列表"""
        biases = []
        raw_biases = parsed.get("biases", []) if isinstance(parsed, dict) else parsed if isinstance(parsed, list) else []

        for item in raw_biases:
            if not isinstance(item, dict):
                continue

            bias_type_str = item.get("bias_type", "")
            bias_type = BIAS_TYPE_MAP.get(bias_type_str, BiasType.LOSS_AVERSION)

            try:
                bias = BiasItem(
                    bias_type=bias_type,
                    bias_name_cn=item.get("bias_name_cn", bias_type_str),
                    severity=min(1.0, max(0.0, float(item.get("severity", 0.5)))),
                    evidence=item.get("evidence", ""),
                    explanation=item.get("explanation", ""),
                    suggestion=item.get("suggestion", ""),
                )
                biases.append(bias)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse bias item: {e}")

        # 按严重程度降序排列
        biases.sort(key=lambda b: b.severity, reverse=True)
        return biases

    def detect_with_rule(self, decision: Decision) -> list[BiasItem]:
        """基于规则的快速偏误检测（无需 LLM，可作为辅助或 fallback）"""
        biases: list[BiasItem] = []
        context = decision.context

        # 损失厌恶：是否出现"万一""失去""不敢"等词
        loss_keywords = ["万一", "失去", "不敢", "害怕失去", "舍不得"]
        if any(kw in context for kw in loss_keywords):
            biases.append(BiasItem(
                bias_type=BiasType.LOSS_AVERSION,
                bias_name_cn="损失厌恶",
                severity=0.4,
                evidence="文本包含'万一/失去/不敢'等回避性表述",
                explanation="损失厌恶是行为经济学中的经典偏误——人们对'失去'的痛苦约为'得到'的快乐的两倍。",
                suggestion="尝试把'失去什么'和'得到什么'分别列出，客观对比。",
            ))

        # 确认偏误：是否只提到某一方的理由
        if len([o for o in decision.options if o.pros]) > 0 and len(decision.options) < 2:
            biases.append(BiasItem(
                bias_type=BiasType.CONFIRMATION_BIAS,
                bias_name_cn="确认偏误",
                severity=0.5,
                evidence="只详细描述了一个选项的理由，缺少其他选项的充分分析",
                explanation="确认偏误让人倾向于寻找支持自己已有倾向的信息，忽略反对证据。",
                suggestion="刻意花时间列出与你现在倾向相反的 3 个理由。",
            ))

        return biases
