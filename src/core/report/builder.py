"""报告构建器 — 将分析结果组装为结构化报告"""

from __future__ import annotations

from typing import Optional

from config.prompts.analyzer import build_report_prompt
from src.llm.client import LLMResponse, get_llm_client
from src.models.decision import Decision
from src.models.report import (
    AnalysisReport,
    BiasItem,
    DecisionStyleAnalysis,
    Question,
    ScenarioAnalysis,
)
from src.utils.logger import logger


class ReportBuilder:
    """将分析引擎的各模块输出组装为完整报告"""

    def __init__(self, llm_client=None):
        self.llm = llm_client or get_llm_client()

    def build(
        self,
        decision: Decision,
        tree_summary: str = "",
        biases: Optional[list[BiasItem]] = None,
        style: Optional[DecisionStyleAnalysis] = None,
        questions: Optional[list[Question]] = None,
    ) -> AnalysisReport:
        """构建完整分析报告

        组合所有分析结果，可选地用 LLM 生成叙事化报告文本。
        """
        biases = biases or []
        questions = questions or []

        # 构建各选项分析
        scenario_analyses = self._build_scenario_analyses(
            decision=decision,
            biases=biases,
        )

        # 提取核心洞察
        key_insight = self._extract_key_insight(
            tree_summary=tree_summary,
            biases=biases,
            style=style,
        )

        # 构造报告
        report = AnalysisReport(
            decision_id=decision.id,
            decision_tree_summary=tree_summary or decision.title,
            scenario_analyses=scenario_analyses,
            biases=biases,
            decision_style=style,
            questions=questions,
            key_insight=key_insight,
            llm_model_used=self.llm.default_model if hasattr(self.llm, 'default_model') else "",
        )

        return report

    def build_narrative_report(
        self,
        decision: Decision,
        report: AnalysisReport,
    ) -> str:
        """生成叙事化的报告文本（用于前端展示）

        调用 LLM 将结构化数据转化为有温度的叙述。
        """
        # 准备各部分的文本摘要
        scenario_text = "\n".join(
            f"**{s.option_label}**: {s.emotional_trajectory}\n"
            f"  风险: {', '.join(s.key_risks[:3])}\n"
            f"  机会: {', '.join(s.key_opportunities[:3])}"
            for s in report.scenario_analyses
        ) or "暂未生成选项分析"

        bias_text = "\n".join(
            f"- {b.bias_name_cn} (严重度: {b.severity:.1f}): {b.explanation}"
            for b in report.biases[:4]
        ) or "暂未检测到明显偏误"

        style_text = (
            f"风格: {report.decision_style.style_description}"
            if report.decision_style else "暂未分析"
        )

        questions_text = "\n".join(
            f"- {q.question} [{q.category}]"
            for q in report.questions[:5]
        ) or "暂未生成追问"

        system, messages = build_report_prompt(
            title=decision.title,
            tree_summary=report.decision_tree_summary,
            scenario_analyses=scenario_text,
            bias_summary=bias_text,
            style_info=style_text,
            questions_summary=questions_text,
            age_range=getattr(decision, 'age_range', ""),
            occupation=getattr(decision, 'occupation_category', ""),
            city=getattr(decision, 'city_tier', ""),
        )

        response = self.llm.chat(
            system=system,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )

        if response.success:
            return response.content
        return self._fallback_text_report(report)

    def _build_scenario_analyses(
        self,
        decision: Decision,
        biases: list[BiasItem],
    ) -> list[ScenarioAnalysis]:
        """基于决策信息和偏误，构造各选项的初步分析"""
        analyses = []
        for i, option in enumerate(decision.options):
            # 找出与此选项相关的偏误
            related_biases = biases[:2]  # 简化：取前两个偏误

            # 构造分析
            analysis = ScenarioAnalysis(
                option_label=option.label,
                emotional_trajectory=f"选择此选项后，预计会经历'期待→不确定→适应'的心理过程。"
                if option.pros else "暂需更多信息来预测心理轨迹。",
                key_risks=option.cons[:3] if option.cons else ["需要用户补充更多信息"],
                key_opportunities=option.pros[:3] if option.pros else ["需要用户补充更多信息"],
                best_case="",
                worst_case="",
                regret_warning="",
            )

            # 如果有偏误，构造后悔警告
            if related_biases:
                bias_hints = "、".join(b.bias_name_cn for b in related_biases)
                analysis.regret_warning = (
                    f"注意你的{bias_hints}偏误可能影响判断。建议在做出决定前，"
                    f"先针对这些偏误做一次客观复盘。"
                )

            analyses.append(analysis)

        return analyses

    def _extract_key_insight(
        self,
        tree_summary: str = "",
        biases: Optional[list[BiasItem]] = None,
        style: Optional[DecisionStyleAnalysis] = None,
    ) -> str:
        """从分析结果中提取最关键的一条洞察"""
        biases = biases or []
        insights = []

        if biases:
            top_bias = max(biases, key=lambda b: b.severity, default=None)
            if top_bias and top_bias.severity > 0.5:
                insights.append(
                    f"你目前最需要警惕的是「{top_bias.bias_name_cn}」——{top_bias.suggestion}"
                )

        if style:
            insights.append(
                f"你的决策风格偏向「{style.style_description}」，{style.advice[:50]}"
            )

        return insights[0] if insights else "保持客观，在做决定前给自己多一些思考时间。"

    def _fallback_text_report(self, report: AnalysisReport) -> str:
        """当 LLM 生成失败时的纯模板报告"""
        lines = []
        lines.append(f"## 📋 核心洞察\n{report.key_insight}\n")
        lines.append(f"## 🔀 你的选择分支\n{report.decision_tree_summary}\n")

        if report.biases:
            lines.append("## 🧠 思维盲区\n")
            for b in report.biases:
                lines.append(f"- **{b.bias_name_cn}** (严重度: {b.severity:.0%})")
                lines.append(f"  - 证据: {b.evidence}")
                lines.append(f"  - 建议: {b.suggestion}\n")

        if report.questions:
            lines.append("## 💭 值得追问自己的问题\n")
            for q in report.questions[:5]:
                lines.append(f"- {q.question}")

        return "\n".join(lines)
