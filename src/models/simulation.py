"""模拟相关数据模型 — Phase 1-2 用，留空供后续开发"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# For SimulationResult only — avoids circular import
from src.models.user import BigFive  # noqa: F401


class EmotionalState(BaseModel):
    """心理状态向量"""
    satisfaction: float = Field(default=0.5, ge=0, le=1, description="满意度")
    anxiety: float = Field(default=0.5, ge=0, le=1, description="焦虑度")
    regret: float = Field(default=0, ge=0, le=1, description="后悔度")
    hope: float = Field(default=0.5, ge=0, le=1, description="希望感")


class AgentType(str, Enum):
    """智能体类型"""
    PROTAGONIST = "protagonist"       # 主角（用户化身）
    PARTNER = "partner"              # 伴侣
    FAMILY = "family"                # 家庭成员
    FRIEND = "friend"                # 朋友
    COLLEAGUE = "colleague"          # 同事
    HR = "hr"                        # HR/面试官
    NPC = "npc"                      # 其他NPC


class AgentState(BaseModel):
    """智能体状态"""
    agent_id: str
    agent_type: AgentType
    name: str
    emotional_state: EmotionalState = Field(default_factory=EmotionalState)
    relationship_with_protagonist: float = Field(default=0.5, ge=-1, le=1)
    memory_summary: str = ""


class TimeSlice(BaseModel):
    """一个时间片的状态快照"""
    week: int
    emotional_state: EmotionalState
    key_event: Optional[str] = None
    event_impact: float = Field(default=0, ge=-1, le=1)
    agent_states: dict[str, AgentState] = Field(default_factory=dict)
    summary: str = ""


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SimulationState(BaseModel):
    """模拟运行的状态"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    option_label: str
    current_week: int = 0
    total_weeks: int = 12
    timeline: list[TimeSlice] = Field(default_factory=list)
    status: SimulationStatus = SimulationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class KeyMoment(BaseModel):
    """关键事件"""
    week: int
    moment_type: str  # "regret_peak" / "opportunity" / "conflict" / "breakthrough"
    description: str
    emotional_impact: float = Field(default=0, ge=-1, le=1)
    probability_actual: float = Field(default=0.5, ge=0, le=1)


class EmotionalCurve(BaseModel):
    """心理状态曲线（用于前端绘图）"""
    weeks: list[int]
    satisfaction: list[float]
    anxiety: list[float]
    regret: list[float]
    hope: list[float]
    key_moments: list[KeyMoment] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """一次完整的模拟结果（支持任意数量选项）"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    decision_title: str = ""
    big_five: Optional[BigFive] = None

    # 各个选项的模拟状态
    states: list[SimulationState] = Field(default_factory=list)
    curves: list[EmotionalCurve] = Field(default_factory=list)
    option_labels: list[str] = Field(default_factory=list)

    status: SimulationStatus = SimulationStatus.PENDING
    timing_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
