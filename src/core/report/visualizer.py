"""图表数据生成 — 为前端提供可视化数据

Phase 0 版本暂只生成基础的结构化数据，供前端 Plotly 渲染。
Phase 1+ 会加入心理状态曲线等复杂图表。
"""

from __future__ import annotations

from src.models.report import AnalysisReport


class Visualizer:
    """生成前端所需的结构化图表数据"""

    @staticmethod
    def bias_radar_data(report: AnalysisReport) -> dict:
        """生成偏误雷达图数据"""
        labels = []
        values = []
        for b in report.biases:
            labels.append(b.bias_name_cn)
            values.append(round(b.severity * 100))
        return {"labels": labels, "values": values}

    @staticmethod
    def question_distribution(report: AnalysisReport) -> dict:
        """生成追问类别分布"""
        counts: dict[str, int] = {}
        for q in report.questions:
            counts[q.category] = counts.get(q.category, 0) + 1
        return {
            "labels": list(counts.keys()),
            "values": list(counts.values()),
        }
