"""SQLAlchemy ORM 模型定义

Phase 0 只需要存储决策分析和报告历史。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    age_range = Column(String(20), default="")
    occupation_category = Column(String(50), default="")
    city_tier = Column(String(20), default="")
    decision_style = Column(String(20), default="unknown")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    decisions = relationship("DecisionRecord", back_populates="user")


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), default="")
    title = Column(String(200), nullable=False)
    category = Column(String(30), default="other")
    context = Column(Text, nullable=False)
    decision_tree_json = Column(Text, default="")  # JSON 序列化的决策树
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("UserRecord", back_populates="decisions")
    reports = relationship("ReportRecord", back_populates="decision")


class ReportRecord(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    decision_id = Column(String(36), ForeignKey("decisions.id"), nullable=False)
    user_id = Column(String(36), default="")
    key_insight = Column(Text, default="")
    narrative_text = Column(Text, default="")      # LLM 生成的完整报告
    bias_count = Column(Integer, default=0)
    question_count = Column(Integer, default=0)
    decision_style = Column(String(20), default="")
    analysis_time_ms = Column(Integer, default=0)
    llm_model_used = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.now)

    decision = relationship("DecisionRecord", back_populates="reports")


class FeedbackRecord(Base):
    """用户真实决策结果反馈（Phase 3 使用）"""
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=_uuid)
    decision_id = Column(String(36), ForeignKey("decisions.id"), nullable=False)
    chosen_option = Column(String(50), default="")
    satisfaction = Column(Float, default=0.0)      # 0-1 满意度
    regretted = Column(Integer, default=0)          # 0/1
    regret_week = Column(Integer, default=0)        # 第几周开始后悔
    actual_events = Column(Text, default="")        # 真实发生的关键事件
    created_at = Column(DateTime, default=datetime.now)
