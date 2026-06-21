"""FastAPI 依赖注入"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Request

from src.db.database import get_db
from src.db.repositories.decision_repo import DecisionRepository
from src.db.repositories.user_repo import UserRepository


async def get_user_id(request: Request) -> str:
    """获取或创建用户 ID"""
    user_id = request.headers.get("X-User-Id", "")
    if not user_id:
        # 可以从 cookie 或 session 获取
        user_id = request.cookies.get("user_id", "")
    return user_id


async def get_decision_repo() -> AsyncGenerator[DecisionRepository, None]:
    db = get_db()
    async with db.session_scope() as session:
        yield DecisionRepository(session=session)


async def get_user_repo() -> AsyncGenerator[UserRepository, None]:
    db = get_db()
    async with db.session_scope() as session:
        yield UserRepository(session=session)
