"""决策相关数据模型"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Option(BaseModel):
    """一个选择分支"""
    label: str = Field(description="选项标签，如'A：留在现公司'")
    description: str = Field(description="选项详细描述")
    pros: list[str] = Field(default_factory=list, description="优点列表")
    cons: list[str] = Field(default_factory=list, description="缺点列表")


class Factor(BaseModel):
    """影响决策的关键变量"""
    name: str = Field(description="变量名称，如'行业景气度'")
    importance: float = Field(default=0.5, ge=0, le=1, description="用户认为的重要程度")
    uncertainty: float = Field(default=0.5, ge=0, le=1, description="不可控程度")


class DecisionTree(BaseModel):
    """决策树 — LLM 拆解后的结构化表示"""
    root_question: str = Field(description="核心决策问题")
    options: list[Option] = Field(description="各个选项")
    key_factors: list[Factor] = Field(description="关键变量")
    dependencies: list[str] = Field(
        default_factory=list,
        description="各选项之间的依赖关系",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="用户的隐含假设",
    )


class DecisionCategory(str, Enum):
    """决策场景分类"""
    CAREER = "career"              # 职业
    RELATIONSHIP = "relationship"   # 感情
    RELOCATION = "relocation"       # 搬家/换城市
    EDUCATION = "education"         # 求学/考研
    FAMILY = "family"               # 家庭
    HEALTH = "health"               # 健康
    FINANCE = "finance"             # 财务
    OTHER = "other"                 # 其他


class Decision(BaseModel):
    """一个完整的决策请求"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = Field(description="决策标题，如'要不要裸辞考研'")
    category: str = Field(default="other", description="决策类别")
    context: str = Field(description="用户的自由叙述，描述决策背景和纠结")
    options: list[Option] = Field(default_factory=list)
    factors: list[Factor] = Field(default_factory=list)
    decision_tree: Optional[DecisionTree] = None
    # 用户画像（影响分析结果）
    age_range: str = Field(default="", description="年龄段，如'25-30'")
    occupation_category: str = Field(default="", description="职业类别，如'互联网/IT'")
    city_tier: str = Field(default="", description="城市类型，如'一线城市'")
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def has_sufficient_info(self) -> bool:
        """判断是否有足够的信息进行分析"""
        return len(self.context) >= 30


class DecisionCreate(BaseModel):
    """创建决策分析的输入模型"""
    title: str = Field(description="决策标题")
    category: str = Field(default="other", description="决策类别")
    context: str = Field(description="用户的叙述", min_length=10)
    options: list[dict] = Field(default_factory=list, description="选项列表（可选）")
    factors: list[dict] = Field(default_factory=list, description="关键变量（可选）")
    # 用户信息（可选）
    age_range: str = ""
    occupation_category: str = ""
    city_tier: str = ""


class DecisionResponse(BaseModel):
    """API 响应决策信息"""
    id: str
    title: str
    category: str
    context_preview: str
    option_count: int
    created_at: str

    @classmethod
    def from_decision(cls, d: Decision) -> "DecisionResponse":
        return cls(
            id=d.id,
            title=d.title,
            category=d.category,
            context_preview=d.context[:100] + "..." if len(d.context) > 100 else d.context,
            option_count=max(len(d.options), 1),
            created_at=d.created_at.isoformat(),
        )
