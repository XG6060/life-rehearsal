"""HistoryStore 测试 — 本地 SQLite，不需要 API 调用"""

from pathlib import Path

import pytest

from src.db.history_store import HistoryStore
from src.models.decision import DecisionCreate
from src.models.report import AnalysisReport, BiasItem, BiasType
from src.services.decision_service import AnalysisResult


@pytest.fixture
def store(tmp_path: Path) -> HistoryStore:
    """使用临时数据库，测试之间互不干扰"""
    db_path = tmp_path / "test_history.db"
    return HistoryStore(db_path=db_path)


def _make_dummy_result(title: str = "测试") -> AnalysisResult:
    """生成一个假的 AnalysisResult 用于测试"""
    report = AnalysisReport(
        decision_id="test-decision-id",
        decision_tree_summary=f"{title}的决策树摘要",
        biases=[
            BiasItem(
                bias_type=BiasType.LOSS_AVERSION,
                bias_name_cn="损失厌恶",
                severity=0.6,
                evidence="用户说不敢冒险",
                explanation="测试偏误",
                suggestion="测试建议",
            ),
        ],
        questions=[],
        key_insight=f"{title}的核心洞察",
    )
    return AnalysisResult(
        report=report,
        narrative_text=f"这是{title}的完整分析报告正文。",
        llm_stats={},
        timing_ms=12345,
    )


def _dummy_input(title: str = "测试决策") -> DecisionCreate:
    return DecisionCreate(
        title=title,
        category="career",
        context="这是一段用于测试的决策描述文本，长度已经超过三十个字符。",
        age_range="25-30",
        occupation_category="互联网/IT",
        city_tier="一线城市",
    )


class TestHistoryStore:
    def test_empty_store(self, store: HistoryStore):
        """空数据库的 list_all 返回空列表"""
        assert store.list_all() == []

    def test_save_and_list(self, store: HistoryStore):
        """保存一条记录后，列表能查到"""
        result = _make_dummy_result()
        inp = _dummy_input()
        store.save(result, inp)

        records = store.list_all()
        assert len(records) == 1
        assert records[0]["title"] == "测试决策"
        assert records[0]["bias_count"] == 1

    def test_get_full_record(self, store: HistoryStore):
        """get 能查到完整记录"""
        result = _make_dummy_result()
        inp = _dummy_input()
        store.save(result, inp)

        record = store.get(result.report.id)
        assert record is not None
        assert record["narrative_text"] == "这是测试的完整分析报告正文。"
        assert "report_json" in record
        assert "decision_input_json" in record

    def test_load_result(self, store: HistoryStore):
        """从历史记录还原 AnalysisResult 对象"""
        result = _make_dummy_result()
        inp = _dummy_input()
        store.save(result, inp)

        loaded = store.load_result(result.report.id)
        assert loaded is not None
        assert loaded.report.key_insight == "测试的核心洞察"
        assert loaded.narrative_text == "这是测试的完整分析报告正文。"

    def test_load_decision_input(self, store: HistoryStore):
        """从历史记录还原 DecisionCreate 对象"""
        result = _make_dummy_result()
        inp = _dummy_input()
        store.save(result, inp)

        loaded = store.load_decision_input(result.report.id)
        assert loaded is not None
        assert loaded.title == "测试决策"
        assert loaded.age_range == "25-30"
        assert loaded.occupation_category == "互联网/IT"

    def test_user_context_stored(self, store: HistoryStore):
        """验证用户画像字段被保存"""
        result = _make_dummy_result()
        inp = _dummy_input()
        store.save(result, inp)

        record = store.get(result.report.id)
        assert record is not None
        assert "互联网/IT" in record.get("user_context", "")
        assert "一线城市" in record.get("user_context", "")

    def test_multiple_records_ordered(self, store: HistoryStore):
        """多条记录按时间倒序排列"""
        import time
        for i in range(3):
            result = _make_dummy_result(title=f"测试{i}")
            inp = _dummy_input(title=f"决策{i}")
            store.save(result, inp)
            time.sleep(0.01)  # 确保时间戳不同

        records = store.list_all()
        assert len(records) == 3
        # 最新的在前面
        assert records[0]["title"] == "决策2"

    def test_delete_record(self, store: HistoryStore):
        """删除单条记录"""
        result = _make_dummy_result()
        inp = _dummy_input()
        store.save(result, inp)
        assert store.count == 1

        store.delete(result.report.id)
        assert store.count == 0

    def test_count(self, store: HistoryStore):
        """统计总数"""
        assert store.count == 0
        for i in range(5):
            result = _make_dummy_result(title=f"测试{i}")
            inp = _dummy_input(title=f"决策{i}")
            store.save(result, inp)
        assert store.count == 5

    def test_save_without_input(self, store: HistoryStore):
        """不传 decision_input 也能保存"""
        result = _make_dummy_result()
        store.save(result, None)

        records = store.list_all()
        assert len(records) == 1
        assert records[0]["title"] == ""
