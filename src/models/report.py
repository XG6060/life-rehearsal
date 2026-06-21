"""分析报告数据模型"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BiasType(str, Enum):
    """认知偏误类型"""
    LOSS_AVERSION = "loss_aversion"           # 损失厌恶
    CONFIRMATION_BIAS = "confirmation_bias"    # 确认偏误
    OVER_OPTIMISM = "over_optimism"            # 过度乐观
    ANCHORING = "anchoring"                    # 锚定效应
    STATUS_QUO = "status_quo"                  # 现状偏好
    SUNK_COST = "sunk_cost"                    # 沉没成本


class BiasItem(BaseModel):
    """一个偏误检测结果"""
    bias_type: BiasType
    bias_name_cn: str = Field(description="偏误中文名称")
    severity: float = Field(default=0.5, ge=0, le=1, description="严重程度")
    evidence: str = Field(description="用户原话中的证据")
    explanation: str = Field(description="为什么这是偏误")
    suggestion: str = Field(description="如何纠正这个偏误")


class Question(BaseModel):
    """苏格拉底式追问"""
    question: str = Field(description="追问内容")
    category: str = Field(default="clarify", description="类别：clarify/challenge/perspective/deepen")
    reason: str = Field(description="为什么问这个问题")


class ScenarioAnalysis(BaseModel):
    """对单个选项的分析"""
    option_label: str
    emotional_trajectory: str = Field(description="预测的心理变化轨迹")
    key_risks: list[str] = Field(default_factory=list, description="主要风险")
    key_opportunities: list[str] = Field(default_factory=list, description="主要机会")
    best_case: str = Field(default="", description="最好的情况")
    worst_case: str = Field(default="", description="最坏的情况")
    regret_warning: str = Field(default="", description="可能的后悔点")


class DecisionStyleAnalysis(BaseModel):
    """决策风格分析"""
    style: str = Field(description="决策风格类型")
    style_description: str = Field(description="风格描述")
    strengths: list[str] = Field(default_factory=list, description="这种风格的优势")
    blind_spots: list[str] = Field(default_factory=list, description="这种风格的盲区")
    advice: str = Field(default="", description="针对性建议")


class AnalysisReport(BaseModel):
    """完整的决策分析报告"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    user_id: str = ""

    # 核心内容
    decision_tree_summary: str = Field(description="决策树概述")
    scenario_analyses: list[ScenarioAnalysis] = Field(default_factory=list)
    biases: list[BiasItem] = Field(default_factory=list)
    decision_style: Optional[DecisionStyleAnalysis] = None
    questions: list[Question] = Field(default_factory=list)

    # 元数据
    key_insight: str = Field(default="", description="最关键的洞察")
    llm_model_used: str = ""
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def top_bias(self) -> Optional[BiasItem]:
        """返回最严重的偏误"""
        if not self.biases:
            return None
        return max(self.biases, key=lambda b: b.severity)

    @property
    def bias_count(self) -> int:
        return len(self.biases)

    @property
    def has_regret_warning(self) -> bool:
        return any(s.regret_warning for s in self.scenario_analyses)


class ReportResponse(BaseModel):
    """API 响应报告"""
    id: str
    decision_id: str
    key_insight: str
    bias_count: int
    top_bias_name: str
    decision_style: str
    question_count: int
    created_at: str

    @classmethod
    def from_report(cls, r: AnalysisReport) -> "ReportResponse":
        return cls(
            id=r.id,
            decision_id=r.decision_id,
            key_insight=r.key_insight[:100] if r.key_insight else "",
            bias_count=r.bias_count,
            top_bias_name=r.top_bias.bias_name_cn if r.top_bias else "",
            decision_style=r.decision_style.style if r.decision_style else "",
            question_count=len(r.questions),
            created_at=r.created_at.isoformat(),
        )
