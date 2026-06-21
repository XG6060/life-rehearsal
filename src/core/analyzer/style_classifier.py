"""决策风格分类器 — 判断用户的决策风格类型"""

from __future__ import annotations

from typing import Optional

from config.prompts.analyzer import build_style_classifier_prompt
from src.llm.client import LLMResponse, get_llm_client
from src.models.report import DecisionStyleAnalysis
from src.utils.logger import logger
from src.utils.text import safe_json_parse


class StyleClassifier:
    """决策风格分类器"""

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()

    def classify(
        self,
        title: str,
        context: str,
        age_range: str = "",
        occupation: str = "",
        city: str = "",
    ) -> tuple[Optional[DecisionStyleAnalysis], LLMResponse]:
        """分析决策风格

        Returns:
            (DecisionStyleAnalysis | None, LLMResponse)
        """
        system, messages = build_style_classifier_prompt(
            title=title,
            context=context,
            age_range=age_range,
            occupation=occupation,
            city=city,
        )

        response = self.llm.chat(
            system=system,
            messages=messages,
            use_cache=True,
        )
        if not response.success:
            logger.error(f"Style classification LLM call failed: {response.error}")
            return None, response

        parsed = safe_json_parse(response.content)
        if not parsed:
            logger.warning(f"Failed to parse style classification JSON: {response.content[:200]}")
            return None, response

        try:
            analysis = DecisionStyleAnalysis(
                style=parsed.get("style", "rational"),
                style_description=parsed.get("style_description", ""),
                strengths=parsed.get("strengths", []),
                blind_spots=parsed.get("blind_spots", []),
                advice=parsed.get("advice", ""),
            )
            return analysis, response
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Failed to build DecisionStyleAnalysis: {e}")
            return None, response
