"""认知偏误雷达图组件"""

from __future__ import annotations

from typing import Optional

import plotly.graph_objects as go


def render_bias_radar(labels: list[str], values: list[float]) -> go.Figure:
    """渲染偏误雷达图"""
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        marker=dict(color="#e74c3c"),
        name="偏误严重程度",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
            ),
        ),
        showlegend=False,
        margin=dict(l=80, r=80, t=20, b=20),
    )

    return fig


def render_bias_gauge(severity: float, label: str) -> go.Figure:
    """渲染单个偏误的仪表盘"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=severity * 100,
        title={"text": label},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#e74c3c" if severity > 0.6 else "#f39c12"},
            "steps": [
                {"range": [0, 33], "color": "lightgreen"},
                {"range": [33, 66], "color": "yellow"},
                {"range": [66, 100], "color": "salmon"},
            ],
        },
        number={"suffix": "%"},
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=30, b=20),
    )

    return fig
