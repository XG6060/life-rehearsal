"""历史记录持久化 — 使用 SQLite 存储分析结果

与 async SQLAlchemy 层共存，使用标准库 sqlite3（同步），
供 Streamlit 前端直接调用。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config.settings import settings
from src.models.decision import DecisionCreate
from src.models.report import AnalysisReport
from src.models.simulation import EmotionalCurve
from src.services.decision_service import AnalysisResult
from src.utils.logger import logger

# 数据库路径
_HISTORY_DIR = settings.data_dir
_DB_PATH = _HISTORY_DIR / "history.db"


def _build_user_context(
    decision_input: Optional[DecisionCreate],
) -> str:
    """从 DecisionCreate 提取用户画像信息，存为逗号分隔字符串"""
    if not decision_input:
        return ""
    parts = []
    if decision_input.occupation_category:
        parts.append(decision_input.occupation_category)
    if decision_input.city_tier:
        parts.append(decision_input.city_tier)
    if decision_input.age_range:
        parts.append(decision_input.age_range)
    return " · ".join(parts)


class HistoryStore:
    """分析历史记录存储（同步 SQLite）"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── 建表 ──────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id            TEXT PRIMARY KEY,
                    title         TEXT DEFAULT '',
                    category      TEXT DEFAULT '',
                    key_insight   TEXT DEFAULT '',
                    bias_count    INTEGER DEFAULT 0,
                    question_count INTEGER DEFAULT 0,
                    decision_style TEXT DEFAULT '',
                    created_at    TEXT DEFAULT '',
                    -- 完整序列化数据（用于还原查看）
                    report_json   TEXT DEFAULT '{}',
                    narrative_text TEXT DEFAULT '',
                    decision_input_json TEXT DEFAULT '{}'
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_created "
                "ON history(created_at DESC)"
            )
            # 兼容旧表：添加 user_id 和 user_context
            for col in ["user_context TEXT DEFAULT ''", "user_id TEXT DEFAULT ''"]:
                try:
                    conn.execute(f"ALTER TABLE history ADD COLUMN {col}")
                except Exception:
                    pass

            # 模拟结果表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    id            TEXT PRIMARY KEY,
                    decision_title TEXT DEFAULT '',
                    big_five_json  TEXT DEFAULT '{}',
                    curves_json    TEXT DEFAULT '[]',
                    labels_json    TEXT DEFAULT '[]',
                    timing_ms      INTEGER DEFAULT 0,
                    status         TEXT DEFAULT 'completed',
                    created_at     TEXT DEFAULT ''
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sim_created "
                "ON simulations(created_at DESC)"
            )
            # 迁移旧表：添加 curves_json 列（已有则忽略）
            try:
                conn.execute("ALTER TABLE simulations ADD COLUMN curves_json TEXT DEFAULT '[]'")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE simulations ADD COLUMN labels_json TEXT DEFAULT '[]'")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE simulations ADD COLUMN user_id TEXT DEFAULT ''")
            except Exception:
                pass

    # ── 写入 ──────────────────────────────────────────────────────

    def save(
        self,
        result: AnalysisResult,
        decision_input: Optional[DecisionCreate] = None,
        user_id: str = "",
    ) -> None:
        """保存一次分析结果到历史记录"""
        report = result.report
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO history
                    (id, title, category, key_insight, bias_count,
                     question_count, decision_style, created_at,
                     report_json, narrative_text, decision_input_json,
                     user_context, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report.id,
                        decision_input.title if decision_input else "",
                        decision_input.category if decision_input else "",
                        report.key_insight[:200] if report.key_insight else "",
                        report.bias_count,
                        len(report.questions),
                        report.decision_style.style
                        if report.decision_style else "",
                        report.created_at.isoformat(),
                        report.model_dump_json(),
                        result.narrative_text,
                        decision_input.model_dump_json()
                        if decision_input else "{}",
                        _build_user_context(decision_input),
                        user_id,
                    ),
                )
                logger.info(f"History saved: {report.id} — {decision_input.title if decision_input else ''}")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    # ── 查询列表 ──────────────────────────────────────────────────

    def list_all(self, limit: int = 50, user_id: str = "") -> list[dict[str, Any]]:
        """获取当前用户的历史记录列表"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if user_id:
                rows = conn.execute(
                    """
                    SELECT id, title, category, key_insight,
                           bias_count, question_count, decision_style,
                           created_at, user_context
                    FROM history
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, title, category, key_insight,
                           bias_count, question_count, decision_style,
                           created_at, user_context
                    FROM history
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    # ── 获取单条完整数据 ──────────────────────────────────────────

    def get(self, report_id: str) -> Optional[dict[str, Any]]:
        """根据 report_id 获取完整历史记录"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM history WHERE id = ?", (report_id,)
            ).fetchone()
            return dict(row) if row else None

    # ── 还原 AnalysisResult ───────────────────────────────────────

    def load_result(self, report_id: str) -> Optional[AnalysisResult]:
        """从历史记录还原 AnalysisResult 对象（用于展示）"""
        record = self.get(report_id)
        if not record:
            return None
        try:
            report = AnalysisReport.model_validate_json(record["report_json"])
            # 从存储的 decision_input_json 还原 timing_ms（近似值）
            return AnalysisResult(
                report=report,
                narrative_text=record.get("narrative_text", ""),
                llm_stats={},
                timing_ms=0,
            )
        except Exception as e:
            logger.error(f"Failed to load result {report_id}: {e}")
            return None

    def load_decision_input(self, report_id: str) -> Optional[DecisionCreate]:
        """从历史记录还原 DecisionCreate 对象"""
        record = self.get(report_id)
        if not record:
            return None
        try:
            return DecisionCreate.model_validate_json(
                record.get("decision_input_json", "{}")
            )
        except Exception as e:
            logger.error(f"Failed to load decision input {report_id}: {e}")
            return None

    # ── 模拟结果存储 ──────────────────────────────────────────────

    def save_simulation(
        self,
        decision_title: str,
        big_five_json: str,
        curves: list[EmotionalCurve],
        labels: list[str],
        timing_ms: int,
        result_id: str = "",
        status: str = "completed",
        user_id: str = "",
    ) -> None:
        """保存一次模拟结果（支持 N 条曲线）"""
        import json
        import uuid
        sim_id = result_id or str(uuid.uuid4())
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                from datetime import datetime
                curves_json = json.dumps(
                    [c.model_dump() for c in curves],
                    ensure_ascii=False,
                )
                labels_json = json.dumps(labels, ensure_ascii=False)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO simulations
                    (id, decision_title, big_five_json,
                     curves_json, labels_json,
                     timing_ms, status, created_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sim_id,
                        decision_title,
                        big_five_json,
                        curves_json,
                        labels_json,
                        timing_ms,
                        status,
                        datetime.now().isoformat(),
                        user_id,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to save simulation: {e}")

    def get_simulation(self, sim_id: str) -> Optional[dict]:
        """获取单条模拟记录"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM simulations WHERE id = ?", (sim_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_simulations(self, limit: int = 20, user_id: str = "") -> list[dict]:
        """列出当前用户的模拟结果"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if user_id:
                rows = conn.execute(
                    """
                    SELECT id, decision_title, timing_ms, status, created_at
                    FROM simulations
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, decision_title, timing_ms, status, created_at
                    FROM simulations
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    # ── 删除 ──────────────────────────────────────────────────────

    def delete(self, report_id: str) -> bool:
        """删除一条历史记录"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM history WHERE id = ?", (report_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete history {report_id}: {e}")
            return False

    @property
    def count(self) -> int:
        """历史记录总数"""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM history").fetchone()
            return row[0] if row else 0
