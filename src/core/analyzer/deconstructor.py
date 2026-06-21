"""决策树拆解器 — 将用户的自然语言描述拆解为结构化决策树"""

from __future__ import annotations

from typing import Any, Optional

from config.prompts.analyzer import build_deconstructor_prompt
from src.llm.client import LLMResponse, get_llm_client
from src.models.decision import Decision, DecisionTree, Factor, Option
from src.utils.logger import logger
from src.utils.text import safe_json_parse


class Deconstructor:
    """决策树拆解器"""

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()

    def deconstruct(self, decision: Decision) -> tuple[Optional[DecisionTree], LLMResponse]:
        """将 Decision 对象拆解为 DecisionTree

        Returns:
            (DecisionTree | None, LLMResponse) — 拆解结果和原始 LLM 响应
        """
        if not decision.has_sufficient_info:
            logger.warning(f"Insufficient info for deconstruction: {decision.id}")
            return None, LLMResponse(
                content="",
                model="",
                error="Insufficient information: context too short",
            )

        # 构造选项和因素的字典格式
        options_dict = [
            {"label": o.label, "description": o.description}
            for o in decision.options
        ] if decision.options else None

        factors_dict = [
            {"name": f.name, "importance": f.importance, "uncertainty": f.uncertainty}
            for f in decision.factors
        ] if decision.factors else None

        # 构建 prompt
        system, messages = build_deconstructor_prompt(
            title=decision.title,
            context=decision.context,
            options=options_dict,
            factors=factors_dict,
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
            logger.error(f"Deconstruction LLM call failed: {response.error}")
            return None, response

        # 解析 JSON
        parsed = safe_json_parse(response.content)
        if not parsed:
            logger.warning(f"Failed to parse deconstruction JSON: {response.content[:200]}")
            # 返回一个基本的决策树
            return self._fallback_tree(decision), response

        # 构建 DecisionTree
        tree = self._parse_tree(parsed, decision)
        return tree, response

    def deconstruct_from_text(
        self,
        title: str,
        context: str,
        options: list[dict[str, Any]] | None = None,
        factors: list[dict[str, Any]] | None = None,
    ) -> tuple[Optional[DecisionTree], LLMResponse]:
        """直接从文本拆解决策树（不创建 Decision 对象）"""
        system, messages = build_deconstructor_prompt(
            title=title,
            context=context,
            options=options,
            factors=factors,
        )

        response = self.llm.chat(system=system, messages=messages, use_cache=True)
        if not response.success:
            return None, response

        parsed = safe_json_parse(response.content)
        if not parsed:
            return None, response

        return self._parse_tree(parsed), response

    def _parse_tree(
        self,
        parsed: dict[str, Any],
        decision: Optional[Decision] = None,
    ) -> DecisionTree:
        """将 LLM 返回的 JSON 解析为 DecisionTree"""
        options = []
        for opt in parsed.get("options", []):
            options.append(Option(
                label=opt.get("label", "未命名选项"),
                description=opt.get("description", ""),
                pros=opt.get("pros", []),
                cons=opt.get("cons", []),
            ))

        factors = []
        for fac in parsed.get("key_factors", []):
            factors.append(Factor(
                name=fac.get("name", "未命名因素"),
                importance=float(fac.get("importance", 0.5)),
                uncertainty=float(fac.get("uncertainty", 0.5)),
            ))

        return DecisionTree(
            root_question=parsed.get("root_question", decision.title if decision else ""),
            options=options,
            key_factors=factors,
            assumptions=parsed.get("assumptions", []),
        )

    def _fallback_tree(self, decision: Decision) -> DecisionTree:
        """当 LLM 解析失败时，基于已有数据构建基本决策树"""
        options = decision.options or [
            Option(label="选项A", description="请补充描述"),
            Option(label="选项B", description="请补充描述"),
        ]
        # 确保至少有两个选项
        if len(options) < 2:
            options.append(Option(label="选项B", description="不做任何改变"))

        factors = decision.factors or [
            Factor(name="具体可行性", importance=0.7, uncertainty=0.5),
            Factor(name="个人意愿", importance=0.6, uncertainty=0.4),
        ]

        return DecisionTree(
            root_question=decision.title,
            options=options,
            key_factors=factors,
            assumptions=["暂未识别出隐含假设"],
        )
