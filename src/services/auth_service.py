"""用户认证服务 — 注册/登录/Session 管理

使用 bcrypt 哈希密码，SQLite 存储用户信息。
Streamlit 端用 session_state 管理登录状态。
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import bcrypt

from config.settings import settings
from src.utils.logger import logger

_DB_PATH = settings.data_dir / "accounts.db"


class AuthService:
    """用户认证服务（同步 SQLite）"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id            TEXT PRIMARY KEY,
                    email         TEXT UNIQUE NOT NULL,
                    nickname      TEXT DEFAULT '',
                    password_hash TEXT NOT NULL,
                    created_at    TEXT DEFAULT ''
                )
            """)
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_email "
                "ON accounts(email)"
            )

    # ── 注册 ──────────────────────────────────────────────────────

    def register(self, email: str, password: str, nickname: str = "") -> dict:
        """注册新用户

        Returns:
            {"ok": True, "user": {"id", "email", "nickname"}}
            或 {"ok": False, "error": "..."}
        """
        email = email.strip().lower()
        if not email or "@" not in email:
            return {"ok": False, "error": "邮箱格式不正确"}
        if len(password) < 6:
            return {"ok": False, "error": "密码至少 6 位"}
        if not nickname:
            nickname = email.split("@")[0]

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        try:
            user_id = str(uuid.uuid4())
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "INSERT INTO accounts (id, email, nickname, password_hash, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, email, nickname, password_hash, datetime.now().isoformat()),
                )
            # Initialize credits for new user
            from src.services.credit_service import init_user_credits
            init_user_credits(user_id)
            logger.info(f"User registered: {email}")
            return {
                "ok": True,
                "user": {"id": user_id, "email": email, "nickname": nickname},
            }
        except sqlite3.IntegrityError:
            return {"ok": False, "error": "该邮箱已被注册"}
        except Exception as e:
            logger.error(f"Register failed: {e}")
            return {"ok": False, "error": "注册失败，请重试"}

    # ── 登录 ──────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """用户登录

        Returns:
            {"ok": True, "user": {"id", "email", "nickname"}}
            或 {"ok": False, "error": "..."}
        """
        email = email.strip().lower()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, email, nickname, password_hash FROM accounts WHERE email = ?",
                (email,),
            ).fetchone()

        if row is None:
            return {"ok": False, "error": "邮箱或密码错误"}

        try:
            valid = bcrypt.checkpw(
                password.encode("utf-8"), row["password_hash"].encode("utf-8")
            )
        except Exception:
            valid = False

        if not valid:
            return {"ok": False, "error": "邮箱或密码错误"}

        logger.info(f"User logged in: {email}")
        return {
            "ok": True,
            "user": {
                "id": row["id"],
                "email": row["email"],
                "nickname": row["nickname"],
            },
        }

    # ── 用户信息 ──────────────────────────────────────────────────

    # ── 修改密码 ──────────────────────────────────────────────────

    def change_password(self, user_id: str, old_pwd: str, new_pwd: str) -> dict:
        """修改用户密码"""
        if len(new_pwd) < 6:
            return {"ok": False, "error": "新密码至少 6 位"}

        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT password_hash FROM accounts WHERE id = ?", (user_id,)
            ).fetchone()
            if row is None:
                return {"ok": False, "error": "用户不存在"}

            try:
                valid = bcrypt.checkpw(old_pwd.encode("utf-8"), row[0].encode("utf-8"))
            except Exception:
                valid = False

            if not valid:
                return {"ok": False, "error": "原密码错误"}

            new_hash = bcrypt.hashpw(new_pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            conn.execute(
                "UPDATE accounts SET password_hash = ? WHERE id = ?",
                (new_hash, user_id),
            )
            logger.info(f"Password changed for user {user_id}")
            return {"ok": True}

    def get_user(self, user_id: str) -> Optional[dict]:
        """根据 user_id 获取用户信息"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, email, nickname, created_at FROM accounts WHERE id = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None
