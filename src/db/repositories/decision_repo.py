"""决策数据仓库"""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.db.models import DecisionRecord, ReportRecord
from src.models.decision import Decision, DecisionTree
from src.models.report import AnalysisReport
from src.utils.logger import logger


class DecisionRepository:
    """决策数据持久化操作"""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.db = get_db()
        self._session = session

    async def _get_session(self) -> AsyncSession:
        if self._session is not None:
            return self._session
        return await self.db.get_session()

    async def save_decision(self, decision: Decision) -> bool:
        """保存一次决策分析记录"""
        try:
            session = await self._get_session()
            record = DecisionRecord(
                id=decision.id,
                title=decision.title,
                category=decision.category,
                context=decision.context,
                decision_tree_json=json.dumps(
                    decision.decision_tree.model_dump() if decision.decision_tree else {},
                    ensure_ascii=False,
                ),
                created_at=decision.created_at,
            )
            session.add(record)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save decision {decision.id}: {e}")
            return False

    async def save_report(
        self,
        report: AnalysisReport,
        narrative_text: str = "",
        analysis_time_ms: int = 0,
    ) -> bool:
        """保存分析报告"""
        try:
            session = await self._get_session()
            record = ReportRecord(
                id=report.id,
                decision_id=report.decision_id,
                key_insight=report.key_insight,
                narrative_text=narrative_text,
                bias_count=report.bias_count,
                question_count=len(report.questions),
                decision_style=report.decision_style.style if report.decision_style else "",
                analysis_time_ms=analysis_time_ms,
                llm_model_used=report.llm_model_used,
            )
            session.add(record)
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save report {report.id}: {e}")
            return False

    async def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        session = await self._get_session()
        result = await session.execute(
            select(DecisionRecord).where(DecisionRecord.id == decision_id)
        )
        return result.scalar_one_or_none()

    async def get_report(self, report_id: str) -> Optional[ReportRecord]:
        session = await self._get_session()
        result = await session.execute(
            select(ReportRecord).where(ReportRecord.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_report_by_decision(self, decision_id: str) -> Optional[ReportRecord]:
        session = await self._get_session()
        result = await session.execute(
            select(ReportRecord).where(ReportRecord.decision_id == decision_id)
        )
        return result.scalar_one_or_none()

    async def list_decisions(self, limit: int = 20) -> list[DecisionRecord]:
        session = await self._get_session()
        result = await session.execute(
            select(DecisionRecord)
            .order_by(desc(DecisionRecord.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
