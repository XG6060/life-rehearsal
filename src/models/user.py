"""用户相关数据模型"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DecisionStyle(str, Enum):
    """决策风格类型"""
    RATIONAL = "rational"          # 理性分析型
    INTUITIVE = "intuitive"        # 直觉驱动型
    DEPENDENT = "dependent"        # 依赖他人型
    AVOIDANT = "avoidant"          # 逃避型
    IMPULSIVE = "impulsive"        # 冲动型
    UNKNOWN = "unknown"            # 未识别


class BigFive(BaseModel):
    """大五人格维度 (0-1 连续值)"""
    openness: float = Field(default=0.5, ge=0, le=1, description="开放性")
    conscientiousness: float = Field(default=0.5, ge=0, le=1, description="尽责性")
    extraversion: float = Field(default=0.5, ge=0, le=1, description="外向性")
    agreeableness: float = Field(default=0.5, ge=0, le=1, description="宜人性")
    neuroticism: float = Field(default=0.5, ge=0, le=1, description="神经质")


class UserProfile(BaseModel):
    """用户画像（可匿名化）"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    age_range: str = ""           # "25-30"
    occupation_category: str = "" # "互联网/IT" / "教育" / ...
    city_tier: str = ""           # "一线城市" / "二线城市" / "三线及以下"
    financial_status: str = ""    # "有充足储蓄" / "月光" / "负债"
    big_five: Optional[BigFive] = None
    decision_style: DecisionStyle = DecisionStyle.UNKNOWN
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def anonymize(self) -> UserProfile:
        """返回匿名化副本（移除可能识别身份的信息）"""
        return UserProfile(
            id=self.id,
            age_range=self.age_range,
            occupation_category=self.occupation_category,
            city_tier=self.city_tier,
            financial_status="",       # 隐去财务细节
            big_five=self.big_five,
            decision_style=self.decision_style,
            created_at=self.created_at,
        )


class UserProfileCreate(BaseModel):
    """创建用户画像的输入模型"""
    age_range: str = ""
    occupation_category: str = ""
    city_tier: str = ""
    financial_status: str = ""

    # 简化版大五人格（可选，后续用户可补充完整）
    openness: Optional[float] = None
    conscientiousness: Optional[float] = None
    extraversion: Optional[float] = None
    agreeableness: Optional[float] = None
    neuroticism: Optional[float] = None


class UserProfileResponse(BaseModel):
    """API 响应用户信息"""
    id: str
    age_range: str
    occupation_category: str
    city_tier: str
    decision_style: str
    created_at: str

    @classmethod
    def from_profile(cls, profile: UserProfile) -> "UserProfileResponse":
        return cls(
            id=profile.id,
            age_range=profile.age_range,
            occupation_category=profile.occupation_category,
            city_tier=profile.city_tier,
            decision_style=profile.decision_style.value,
            created_at=profile.created_at.isoformat(),
        )
