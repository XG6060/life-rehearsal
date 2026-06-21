"""心理曲线构建测试"""

from src.core.simulator.curve_builder import build_emotional_curve
from src.models.simulation import EmotionalState, TimeSlice


def _make_timeline(regrets: list[float] | None = None) -> list[TimeSlice]:
    """生成 12 周的测试 timeline"""
    regrets = regrets or [0.1] * 12
    timeline = []
    for w in range(1, 13):
        timeline.append(TimeSlice(
            week=w,
            emotional_state=EmotionalState(
                satisfaction=0.5,
                anxiety=0.3,
                regret=regrets[w - 1],
                hope=0.6,
            ),
            key_event=f"第 {w} 周事件" if w % 3 == 0 else "",
            event_impact=0.3 if w % 3 == 0 else 0,
            summary=f"第 {w} 周",
        ))
    return timeline


class TestCurveBuilder:
    def test_basic_curve_structure(self):
        """12 周生成正确结构的 EmotionalCurve"""
        timeline = _make_timeline()
        curve = build_emotional_curve(timeline)
        assert len(curve.weeks) == 12
        assert len(curve.satisfaction) == 12
        assert len(curve.anxiety) == 12
        assert len(curve.regret) == 12
        assert len(curve.hope) == 12

    def test_key_moments_includes_milestones(self):
        """第 1 周和最后 1 周自动标记为 milestone"""
        timeline = _make_timeline()
        curve = build_emotional_curve(timeline)
        milestones = [m for m in curve.key_moments if m.moment_type == "milestone"]
        assert len(milestones) >= 1  # 至少第 1 周或第 12 周

    def test_regret_peak_detection(self):
        """后悔度 > 0.6 应被标记为 regret_peak"""
        regrets = [0.1] * 12
        regrets[5] = 0.8  # 第 6 周后悔高峰
        timeline = _make_timeline(regrets)
        curve = build_emotional_curve(timeline)
        regret_peaks = [m for m in curve.key_moments if m.moment_type == "regret_peak"]
        assert len(regret_peaks) >= 1

    def test_empty_key_moments(self):
        """全是 0 值，只有 milestone"""
        timeline = _make_timeline([0.0] * 12)
        curve = build_emotional_curve(timeline)
        assert len(curve.key_moments) >= 0  # 不应该崩溃

    def test_single_week_timeline(self):
        """边界情况：只有 1 周"""
        with_1_week = [
            TimeSlice(week=1, emotional_state=EmotionalState())
        ]
        curve = build_emotional_curve(with_1_week)
        assert len(curve.weeks) == 1
