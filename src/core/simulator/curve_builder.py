"""心理曲线构建器 — 从 TimeSlice 列表生成 EmotionalCurve（用于前端绘图）"""

from __future__ import annotations

from src.models.simulation import EmotionalCurve, KeyMoment, TimeSlice


def build_emotional_curve(timeline: list[TimeSlice]) -> EmotionalCurve:
    """从模拟时间线构建心理状态曲线

    Args:
        timeline: 按周排序的 TimeSlice 列表

    Returns:
        EmotionalCurve — 用于前端 Plotly 渲染
    """
    weeks = [t.week for t in timeline]
    satisfaction = [t.emotional_state.satisfaction for t in timeline]
    anxiety = [t.emotional_state.anxiety for t in timeline]
    regret = [t.emotional_state.regret for t in timeline]
    hope = [t.emotional_state.hope for t in timeline]

    key_moments = _extract_key_moments(timeline)

    return EmotionalCurve(
        weeks=weeks,
        satisfaction=satisfaction,
        anxiety=anxiety,
        regret=regret,
        hope=hope,
        key_moments=key_moments,
    )


def _extract_key_moments(timeline: list[TimeSlice]) -> list[KeyMoment]:
    """从 timeline 中提取值得标注的关键事件"""
    key_moments: list[KeyMoment] = []
    prev_satisfaction: float | None = None

    for t in timeline:
        # 第 1 周和最后 1 周自动标注为 milestone
        if t.week == 1 or t.week == len(timeline):
            key_moments.append(KeyMoment(
                week=t.week,
                moment_type="milestone",
                description=t.key_event or ("开始" if t.week == 1 else "模拟终点"),
                emotional_impact=0,
            ))
            continue

        # 后悔峰值
        if t.emotional_state.regret > 0.6:
            key_moments.append(KeyMoment(
                week=t.week,
                moment_type="regret_peak",
                description=t.key_event or "后悔感达到高点",
                emotional_impact=t.event_impact,
            ))

        # 危机（高焦虑 + 低满意）
        elif t.emotional_state.anxiety > 0.7 and t.emotional_state.satisfaction < 0.3:
            key_moments.append(KeyMoment(
                week=t.week,
                moment_type="crisis",
                description=t.key_event or "情绪低谷",
                emotional_impact=t.event_impact,
            ))

        # 突破（满意度大幅上升）
        if prev_satisfaction is not None:
            jump = t.emotional_state.satisfaction - prev_satisfaction
            if jump > 0.15:
                key_moments.append(KeyMoment(
                    week=t.week,
                    moment_type="breakthrough",
                    description=t.key_event or "状态明显好转",
                    emotional_impact=t.event_impact,
                ))

        # 信心高峰
        if t.emotional_state.hope > 0.8 and t.emotional_state.regret < 0.2:
            key_moments.append(KeyMoment(
                week=t.week,
                moment_type="confidence_peak",
                description=t.key_event or "信心高涨",
                emotional_impact=t.event_impact,
            ))

        prev_satisfaction = t.emotional_state.satisfaction

    return key_moments
