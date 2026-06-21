"""模拟引擎 — 逐周用 LLM 推演用户心理状态

核心循环：
  for week 1..12:
    1. 构建本周 prompt（上周状态 + 人格画像 + 决策上下文）
    2. LLM 调用（fast 模型）
    3. 解析 JSON → EmotionalState + key_event
    4. clamp 变化量在 ±0.15 内
    5. 创建 TimeSlice 加入 timeline

两条路径（A/B）各跑一次，独立推进。
"""

from __future__ import annotations

from typing import Optional

from config.prompts.simulator import build_week_prompt
from src.llm.client import LLMClient, get_llm_client
from src.models.decision import Decision
from src.models.simulation import (
    EmotionalState,
    SimulationState,
    SimulationStatus,
    TimeSlice,
)
from src.models.user import BigFive
from src.utils.logger import logger
from src.utils.text import safe_json_parse

# 心理状态变化量的软限制（防止 LLM 输出跳变过大）
_MAX_STATE_CHANGE = 0.15
_DEFAULT_TOTAL_WEEKS = 12


class SimulatorEngine:
    """模拟引擎 — 负责单条路径的逐周推演"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        # 使用 fast 模型配置：较低温度保证模拟稳定性
        self.model = "deepseek-chat"
        self.max_tokens = 2048
        self.temperature = 0.6

    def simulate(
        self,
        decision: Decision,
        option_label: str,
        big_five: BigFive,
        total_weeks: int = _DEFAULT_TOTAL_WEEKS,
    ) -> SimulationState:
        """模拟一条决策路径的完整 12 周心理轨迹

        Args:
            decision: 用户的决策信息（含 title, context, 用户画像）
            option_label: 当前模拟的选项标签，如"A：辞职考研"
            big_five: 大五人格
            total_weeks: 模拟总周数（默认 12）

        Returns:
            SimulationState — 完整的模拟运行状态
        """
        state = SimulationState(
            decision_id=decision.id,
            option_label=option_label,
            status=SimulationStatus.RUNNING,
            total_weeks=total_weeks,
        )

        # 构建用户信息字符串（用于 prompt）
        user_info = _format_user_info(decision)

        # 初始状态：基于人格推导基线
        prev_emotional = self._derive_initial_state(big_five)
        prev_event = ""

        # 第 0 周作为基线
        state.timeline.append(TimeSlice(
            week=0,
            emotional_state=prev_emotional,
            summary="初始基线状态",
        ))

        # 逐周推进
        for week in range(1, total_weeks + 1):
            try:
                result = self._run_week(
                    week=week,
                    total_weeks=total_weeks,
                    decision=decision,
                    option_label=option_label,
                    user_info=user_info,
                    big_five=big_five,
                    prev_emotional=prev_emotional,
                    prev_event=prev_event,
                )
            except Exception as e:
                logger.error(f"Simulation week {week} failed: {e}")
                # 失败时用之前的状态 + 小幅偏移继续
                result = self._fallback_week(prev_emotional, week, str(e))

            # 创建 TimeSlice
            ts = TimeSlice(
                week=week,
                emotional_state=result["emotional"],
                key_event=result["key_event"],
                event_impact=result["event_impact"],
                summary=result["summary"],
            )
            state.timeline.append(ts)
            state.current_week = week

            prev_emotional = result["emotional"]
            prev_event = result["key_event"]

        state.status = SimulationStatus.COMPLETED
        return state

    def _run_week(
        self,
        week: int,
        total_weeks: int,
        decision: Decision,
        option_label: str,
        user_info: str,
        big_five: BigFive,
        prev_emotional: EmotionalState,
        prev_event: str,
    ) -> dict:
        """运行一周的模拟"""
        system, messages = build_week_prompt(
            week=week,
            total_weeks=total_weeks,
            title=decision.title,
            option_label=option_label,
            user_info=user_info,
            openness=big_five.openness,
            conscientiousness=big_five.conscientiousness,
            extraversion=big_five.extraversion,
            agreeableness=big_five.agreeableness,
            neuroticism=big_five.neuroticism,
            prev_satisfaction=prev_emotional.satisfaction,
            prev_anxiety=prev_emotional.anxiety,
            prev_regret=prev_emotional.regret,
            prev_hope=prev_emotional.hope,
            prev_event=prev_event,
        )

        response = self.llm.chat(
            system=system,
            messages=messages,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            use_cache=False,  # 每周场景不同，缓存命中率低
        )

        if not response.success:
            raise RuntimeError(f"LLM call failed: {response.error}")

        parsed = safe_json_parse(response.content)
        if not parsed:
            raise RuntimeError(f"Failed to parse LLM response: {response.content[:200]}")

        # 解析新状态
        new_emotional = self._parse_emotional(parsed, prev_emotional)
        key_event = (parsed.get("key_event") or "").strip()
        event_impact = float(parsed.get("event_impact", 0))
        summary = (parsed.get("summary") or "").strip()

        # clamp event_impact
        event_impact = max(-1.0, min(1.0, event_impact))

        return {
            "emotional": new_emotional,
            "key_event": key_event or _default_event(week, total_weeks),
            "event_impact": event_impact,
            "summary": summary or f"第 {week} 周模拟完成",
        }

    def _parse_emotional(
        self,
        parsed: dict,
        prev: EmotionalState,
    ) -> EmotionalState:
        """解析 LLM 返回的 EmotionalState，带 clamp 保护"""
        raw = EmotionalState(
            satisfaction=float(parsed.get("satisfaction", prev.satisfaction)),
            anxiety=float(parsed.get("anxiety", prev.anxiety)),
            regret=float(parsed.get("regret", prev.regret)),
            hope=float(parsed.get("hope", prev.hope)),
        )

        # clamp 到 [0, 1]
        clamped = EmotionalState(
            satisfaction=max(0.0, min(1.0, raw.satisfaction)),
            anxiety=max(0.0, min(1.0, raw.anxiety)),
            regret=max(0.0, min(1.0, raw.regret)),
            hope=max(0.0, min(1.0, raw.hope)),
        )

        # 强制变化量不超过软限制
        for attr in ("satisfaction", "anxiety", "regret", "hope"):
            old_val = getattr(prev, attr)
            new_val = getattr(clamped, attr)
            diff = new_val - old_val
            if abs(diff) > _MAX_STATE_CHANGE:
                constrained = old_val + (diff / abs(diff)) * _MAX_STATE_CHANGE
                setattr(clamped, attr, max(0.0, min(1.0, constrained)))

        return clamped

    def _fallback_week(
        self,
        prev: EmotionalState,
        week: int,
        error: str,
    ) -> dict:
        """LLM 调用失败时的兜底：小幅随机偏移"""
        import random
        offset = 0.05
        return {
            "emotional": EmotionalState(
                satisfaction=max(0.0, min(1.0, prev.satisfaction + random.uniform(-offset, offset))),
                anxiety=max(0.0, min(1.0, prev.anxiety + random.uniform(-offset, offset))),
                regret=max(0.0, min(1.0, prev.regret + random.uniform(-offset, offset))),
                hope=max(0.0, min(1.0, prev.hope + random.uniform(-offset, offset))),
            ),
            "key_event": "",
            "event_impact": 0.0,
            "summary": f"第 {week} 周分析中断（{error}），沿用趋势估算",
        }

    @staticmethod
    def _derive_initial_state(big_five: BigFive) -> EmotionalState:
        """从 BigFive 推导基线心理状态"""
        return EmotionalState(
            satisfaction=0.5 + (big_five.conscientiousness - 0.5) * 0.3,
            anxiety=0.3 + (big_five.neuroticism - 0.5) * 0.6,
            regret=0.1 + (big_five.neuroticism - 0.5) * 0.2,
            hope=0.6 + (big_five.extraversion - 0.5) * 0.4,
        )


def _format_user_info(decision: Decision) -> str:
    """从 Decision 中提取用户画像文本"""
    parts = []
    if decision.age_range:
        parts.append(f"年龄阶段：{decision.age_range}")
    if decision.occupation_category:
        parts.append(f"职业领域：{decision.occupation_category}")
    if decision.city_tier:
        parts.append(f"所在城市：{decision.city_tier}")
    return "，".join(parts) if parts else "未提供详细个人信息"


def _default_event(week: int, total: int) -> str:
    """当 LLM 未返回关键事件时的默认值"""
    if week == 1:
        return "做出了决定，开始了新的阶段"
    if week == total:
        return "12 周模拟结束"
    return ""
