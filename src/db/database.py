"""数据库连接管理

Phase 0 使用 SQLite (aiosqlite)，Phase 3 可切换至 PostgreSQL。
使用 SQLAlchemy 2.0 async 模式。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config.settings import settings
from src.utils.logger import logger


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


class DatabaseManager:
    """数据库管理器 — 管理连接生命周期"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(
                self.database_url,
                echo=settings.debug,
                poolclass=NullPool,  # SQLite 不需要连接池
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factory

    async def init_db(self) -> None:
        """创建所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database tables created at {self.database_url}")

    async def drop_db(self) -> None:
        """删除所有表（仅用于测试）"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncSession:
        """获取一个新会话"""
        return self.session_factory()

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """上下文管理器：自动提交/回滚"""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine is not None:
            await self._engine.dispose()
            logger.info("Database connection closed")


# ── 全局单例 ───────────────────────────────────────────────────

_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """获取全局数据库管理器"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_database() -> None:
    """初始化数据库（应用启动时调用）"""
    db = get_db()
    await db.init_db()


async def close_database() -> None:
    """关闭数据库（应用关闭时调用）"""
    db = get_db()
    await db.close()
