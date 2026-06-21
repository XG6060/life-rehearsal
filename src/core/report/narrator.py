"""叙事化输出 — 把数据变成故事"""

from __future__ import annotations

from src.models.report import AnalysisReport, BiasItem


class Narrator:
    """将结构化数据转化为可读的叙事文本（Phase 0 轻量版本）"""

    @staticmethod
    def bias_to_text(bias: BiasItem) -> str:
        """将一个偏误转化为人性化的描述"""
        return (
            f"你表现出了「{bias.bias_name_cn}」的倾向。\n"
            f"具体来说，{bias.explanation}\n"
            f"一个建议是：{bias.suggestion}"
        )

    @staticmethod
    def report_summary(report: AnalysisReport) -> str:
        """生成报告的简短摘要（用于分享/预览）"""
        bias_count = len(report.biases)
        question_count = len(report.questions)
        style_name = report.decision_style.style_description if report.decision_style else "未确定"

        return (
            f"分析了你的决策后，我发现了 {bias_count} 个可能的思维盲区，"
            f"准备了 {question_count} 个值得追问自己的问题。"
            f"你的决策风格偏向「{style_name}」。\n\n"
            f"最关键的发现：{report.key_insight}"
        )

    @staticmethod
    def regret_warning_to_text(report: AnalysisReport) -> str:
        """生成后悔预警文本"""
        if not report.has_regret_warning:
            return "暂未识别出明显的高后悔风险因素。"

        warnings = []
        for s in report.scenario_analyses:
            if s.regret_warning:
                warnings.append(f"**{s.option_label}**: {s.regret_warning}")

        return "\n\n".join(warnings)
