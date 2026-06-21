"""心理状态曲线图组件 — 用于展示模拟结果（Phase 1+）"""

from __future__ import annotations

from typing import Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.models.simulation import EmotionalCurve


def render_emotional_curve(curve: EmotionalCurve) -> go.Figure:
    """渲染心理状态曲线"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=curve.weeks,
        y=curve.satisfaction,
        name="满意度",
        line=dict(color="#2ecc71", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=curve.weeks,
        y=curve.anxiety,
        name="焦虑度",
        line=dict(color="#e74c3c", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=curve.weeks,
        y=curve.regret,
        name="后悔度",
        line=dict(color="#f39c12", width=3, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=curve.weeks,
        y=curve.hope,
        name="希望感",
        line=dict(color="#3498db", width=3),
    ))

    # 标注关键事件（去重 + 交替上下位置防重叠）
    seen_weeks = set()
    pos_index = 0
    positions = ["top", "bottom"]
    important_types = {"regret_peak", "breakthrough", "crisis", "confidence_peak"}
    for moment in curve.key_moments:
        if moment.week in seen_weeks:
            continue
        if moment.moment_type not in important_types:
            continue
        seen_weeks.add(moment.week)
        pos = positions[pos_index % 2]
        pos_index += 1
        fig.add_vline(
            x=moment.week,
            line_dash="dot",
            line_color="gray",
            annotation_text=moment.description[:18],
            annotation_position=pos,
        )

    fig.update_layout(
        title="心理状态模拟曲线",
        xaxis_title="周数",
        yaxis_title="程度 (0-1)",
        yaxis_range=[0, 1],
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    return fig


def render_comparison_chart(
    curves: list[EmotionalCurve],
    labels: list[str],
) -> go.Figure:
    """各维度分开展示，2×2 子图布局

    每个子图一个维度（满意度/焦虑度/后悔度/希望感），
    把所有选项曲线画在同一张子图上对比，清晰不拥挤。
    """
    base_hues = [0, 120, 240, 60, 300, 180]
    colors = {labels[i] if i < len(labels) else f"#{i}":
              f"hsl({base_hues[i % len(base_hues)]}, 55%, 40%)"
              for i in range(len(curves))}

    dim_config = [
        ("satisfaction", "😊 满意度", 0, 0),
        ("anxiety", "😰 焦虑度", 0, 1),
        ("regret", "😖 后悔度", 1, 0),
        ("hope", "💪 希望感", 1, 1),
    ]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[d[1] for d in dim_config],
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )

    for i, (curve, label) in enumerate(zip(curves, labels)):
        color = colors.get(label, "#333")
        for dim_name, _, row, col in dim_config:
            yvals = getattr(curve, dim_name, [])
            dash = "dash" if dim_name == "regret" else "solid"
            fig.add_trace(
                go.Scatter(
                    x=curve.weeks, y=yvals,
                    name=label,
                    legendgroup=label,
                    line=dict(color=color, width=2.5, dash=dash),
                    showlegend=(dim_name == "satisfaction"),  # 只在第一张子图显示图例
                ),
                row=row + 1, col=col + 1,
            )

    fig.update_layout(
        height=500,
        title_text=f"{len(curves)} 个选项心理状态对比",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="right", x=1),
        margin=dict(l=30, r=30, t=60, b=30),
        dragmode=False,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_yaxes(range=[0, 1], row=1, col=1)
    fig.update_yaxes(range=[0, 1], row=1, col=2)
    fig.update_yaxes(range=[0, 1], row=2, col=1)
    fig.update_yaxes(range=[0, 1], row=2, col=2)
    return fig


def render_empty_chart() -> go.Figure:
    """渲染空曲线图（占位用）"""
    fig = go.Figure()
    fig.add_annotation(
        text="模拟尚未运行",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
