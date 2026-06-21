"""Pydantic 数据模型测试"""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.models.decision import Decision, DecisionCreate, Option, Factor, DecisionTree
from src.models.report import AnalysisReport, BiasItem, BiasType, Question, ScenarioAnalysis
from src.models.user import BigFive, UserProfile, DecisionStyle


class TestDecisionModels:
    def test_option_defaults(self):
        opt = Option(label="A：辞职", description="辞职备考")
        assert opt.label == "A：辞职"
        assert opt.pros == []
        assert opt.cons == []

    def test_decision_create_minimal(self):
        d = DecisionCreate(title="测试", context="这是一段超过十个字的测试描述文本")
        assert d.title == "测试"
        assert d.category == "other"
        assert d.age_range == ""

    def test_decision_create_too_short(self):
        with pytest.raises(ValidationError):
            DecisionCreate(title="测试", context="太短")

    def test_decision_auto_fields(self):
        d = Decision(title="测试", context="x" * 30)
        assert d.id  # 自动生成 UUID
        assert d.created_at  # 自动生成时间
        # 验证 UUID 格式
        UUID(d.id)

    def test_decision_has_sufficient_info(self):
        short = Decision(title="短", context="x" * 20)
        assert not short.has_sufficient_info

        long_enough = Decision(title="够长", context="x" * 30)
        assert long_enough.has_sufficient_info

    def test_decision_with_user_info(self):
        d = Decision(
            title="测试决策",
            context="x" * 30,
            age_range="25-30",
            occupation_category="互联网/IT",
            city_tier="一线城市",
        )
        assert d.age_range == "25-30"
        assert d.occupation_category == "互联网/IT"
        assert d.city_tier == "一线城市"

    def test_decision_tree(self):
        tree = DecisionTree(
            root_question="要不要换工作",
            options=[
                Option(label="A：留下", description="留在现公司"),
                Option(label="B：跳槽", description="去新公司"),
            ],
            key_factors=[
                Factor(name="薪资涨幅", importance=0.8, uncertainty=0.3),
            ],
        )
        assert len(tree.options) == 2
        assert len(tree.key_factors) == 1
        assert tree.assumptions == []


class TestReportModels:
    def test_bias_item_severity_too_high(self):
        """severity 超出范围应报错（Pydantic v2 严格校验，不自动 clamp）"""
        with pytest.raises(ValidationError):
            BiasItem(
                bias_type=BiasType.LOSS_AVERSION,
                bias_name_cn="损失厌恶",
                severity=1.5,
                evidence="测试",
                explanation="测试",
                suggestion="测试建议",
            )

    def test_bias_item_severity_too_low(self):
        with pytest.raises(ValidationError):
            BiasItem(
                bias_type=BiasType.LOSS_AVERSION,
                bias_name_cn="损失厌恶",
                severity=-0.5,
                evidence="测试",
                explanation="测试",
                suggestion="测试建议",
            )

    def test_question_categories(self):
        q = Question(
            question="你真的需要这个吗？",
            category="challenge",
            reason="帮助用户反思",
        )
        assert q.category == "challenge"

    def test_analysis_report_top_bias(self):
        report = AnalysisReport(
            decision_id="test",
            decision_tree_summary="测试摘要",
            biases=[
                BiasItem(
                    bias_type=BiasType.SUNK_COST,
                    bias_name_cn="沉没成本",
                    severity=0.8,
                    evidence="用户说'已经投入了三年'",
                    explanation="测试",
                    suggestion="测试",
                ),
                BiasItem(
                    bias_type=BiasType.LOSS_AVERSION,
                    bias_name_cn="损失厌恶",
                    severity=0.3,
                    evidence="用户说'不敢冒险'",
                    explanation="测试",
                    suggestion="测试",
                ),
            ],
        )
        assert report.bias_count == 2
        assert report.top_bias.bias_type == BiasType.SUNK_COST  # 严重度最高

    def test_analysis_report_no_bias(self):
        report = AnalysisReport(
            decision_id="test",
            decision_tree_summary="测试",
        )
        assert report.bias_count == 0
        assert report.top_bias is None


class TestUserModels:
    def test_big_five_defaults(self):
        bf = BigFive()
        assert bf.openness == 0.5
        assert bf.conscientiousness == 0.5

    def test_user_profile_anonymize(self):
        profile = UserProfile(
            age_range="25-30",
            occupation_category="互联网/IT",
            city_tier="一线城市",
            financial_status="有充足储蓄",
        )
        anonymized = profile.anonymize()
        assert anonymized.financial_status == ""  # 财务信息被隐去
        assert anonymized.age_range == "25-30"  # 其他信息保留
