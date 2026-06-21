"""用户数据仓库"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.db.models import UserRecord


class UserRepository:
    """用户数据持久化操作"""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.db = get_db()
        self._session = session

    async def _get_session(self) -> AsyncSession:
        if self._session is not None:
            return self._session
        return await self.db.get_session()

    async def create(self, user_id: str, **kwargs) -> UserRecord:
        session = await self._get_session()
        record = UserRecord(id=user_id, **kwargs)
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def get_by_id(self, user_id: str) -> Optional[UserRecord]:
        session = await self._get_session()
        result = await session.execute(
            select(UserRecord).where(UserRecord.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_style(self, user_id: str, style: str) -> bool:
        session = await self._get_session()
        result = await session.execute(
            select(UserRecord).where(UserRecord.id == user_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return False
        record.decision_style = style
        await session.commit()
        return True
