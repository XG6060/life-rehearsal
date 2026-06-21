"""信用额度服务 — 基于 token 消耗计费，管理用户余额

定价模型：
- DeepSeek 输入: ¥0.001/1K tokens, 输出: ¥0.004/1K tokens
- 用户价格 = DeepSeek 成本 × 1.5
- 新用户赠送 1 次分析 + 1 次模拟
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import settings
from src.utils.logger import logger

DB_PATH = settings.data_dir / "credits.db"

# 成本估算（元/1K tokens）
COST_PER_1K_INPUT = 0.001   # ¥0.001
COST_PER_1K_OUTPUT = 0.004  # ¥0.004
MARKUP = 1.5                 # ×1.5 利润

# 估算每次消耗
EST_ANALYSIS_INPUT = 6000   # ~6K input tokens
EST_ANALYSIS_OUTPUT = 4000  # ~4K output tokens
EST_SIMULATION_INPUT = 12000 # ~12K input (24 weeks × 500 tokens)
EST_SIMULATION_OUTPUT = 6000 # ~6K output

# 免费额度
FREE_ANALYSIS_COUNT = 1
FREE_SIMULATION_COUNT = 1

# 充值档位
RECHARGE_OPTIONS = [
    {"label": "¥1 — 约 30 次分析", "amount": 1.0},
    {"label": "¥5 — 约 150 次分析", "amount": 5.0},
    {"label": "¥10 — 约 300 次分析", "amount": 10.0},
    {"label": "¥20 — 约 600 次分析", "amount": 20.0},
]

def _init_db():
    db_path = DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_credits (
                user_id TEXT PRIMARY KEY,
                balance REAL DEFAULT 0.0,
                free_analysis INTEGER DEFAULT 0,
                free_simulation INTEGER DEFAULT 0,
                total_changed REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                tx_type TEXT DEFAULT 'deduct',
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_user ON credit_transactions(user_id)")

_init_db()

def init_user_credits(user_id: str) -> None:
    """新用户注册时初始化信用额度"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute(
            """INSERT OR IGNORE INTO user_credits
               (user_id, balance, free_analysis, free_simulation, updated_at)
               VALUES (?, 0.0, ?, ?, ?)""",
            (user_id, FREE_ANALYSIS_COUNT, FREE_SIMULATION_COUNT, datetime.now().isoformat()),
        )

def get_credits(user_id: str) -> dict:
    """获取用户信用信息"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM user_credits WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is None:
            init_user_credits(user_id)
            return get_credits(user_id)
        return dict(row)

def has_free_analysis(user_id: str) -> bool:
    return get_credits(user_id).get("free_analysis", 0) > 0

def has_free_simulation(user_id: str) -> bool:
    return get_credits(user_id).get("free_simulation", 0) > 0

def can_afford_analysis(user_id: str) -> bool:
    """检查用户是否能做一次分析"""
    if has_free_analysis(user_id):
        return True
    creds = get_credits(user_id)
    return creds.get("balance", 0) >= estimate_analysis_cost()

def can_afford_simulation(user_id: str) -> bool:
    """检查用户是否能做一次模拟"""
    if has_free_simulation(user_id):
        return True
    creds = get_credits(user_id)
    return creds.get("balance", 0) >= estimate_simulation_cost()

def estimate_analysis_cost() -> float:
    return (EST_ANALYSIS_INPUT * COST_PER_1K_INPUT / 1000
            + EST_ANALYSIS_OUTPUT * COST_PER_1K_OUTPUT / 1000) * MARKUP

def estimate_simulation_cost() -> float:
    return (EST_SIMULATION_INPUT * COST_PER_1K_INPUT / 1000
            + EST_SIMULATION_OUTPUT * COST_PER_1K_OUTPUT / 1000) * MARKUP

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """根据实际 token 消耗计算费用（元）"""
    cost = (input_tokens * COST_PER_1K_INPUT / 1000
            + output_tokens * COST_PER_1K_OUTPUT / 1000) * MARKUP
    return round(cost, 4)

def deduct_analysis(user_id: str, input_tokens: int = 0, output_tokens: int = 0) -> dict:
    """扣减一次分析的费用"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT free_analysis, balance FROM user_credits WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row is None:
            return {"ok": False, "error": "账户不存在"}

        free = row[0]
        amount = calculate_cost(input_tokens, output_tokens) if (input_tokens or output_tokens) else estimate_analysis_cost()

        if free > 0:
            conn.execute(
                "UPDATE user_credits SET free_analysis = free_analysis - 1, updated_at = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id),
            )
            conn.execute(
                "INSERT INTO credit_transactions (user_id, amount, tx_type, description, created_at) VALUES (?, 0, 'free', '免费分析', ?)",
                (user_id, datetime.now().isoformat()),
            )
            return {"ok": True, "free": True, "amount": 0}

        if row[1] >= amount:
            conn.execute(
                "UPDATE user_credits SET balance = balance - ?, total_changed = total_changed + ?, updated_at = ? WHERE user_id = ?",
                (amount, amount, datetime.now().isoformat(), user_id),
            )
            conn.execute(
                "INSERT INTO credit_transactions (user_id, amount, tx_type, description, created_at) VALUES (?, ?, 'deduct', ?, ?)",
                (user_id, -amount, "分析报告", datetime.now().isoformat()),
            )
            return {"ok": True, "free": False, "amount": amount}

        return {"ok": False, "error": f"余额不足，需要 ¥{amount:.2f}，当前 ¥{row[1]:.2f}"}

def deduct_simulation(user_id: str, input_tokens: int = 0, output_tokens: int = 0) -> dict:
    """扣减一次模拟的费用"""
    with sqlite3.connect(str(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT free_simulation, balance FROM user_credits WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row is None:
            return {"ok": False, "error": "账户不存在"}

        free = row[0]
        amount = calculate_cost(input_tokens, output_tokens) if (input_tokens or output_tokens) else estimate_analysis_cost()

        if free > 0:
            conn.execute(
                "UPDATE user_credits SET free_simulation = free_simulation - 1, updated_at = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id),
            )
            conn.execute(
                "INSERT INTO credit_transactions (user_id, amount, tx_type, description, created_at) VALUES (?, 0, 'free', '免费模拟', ?)",
                (user_id, datetime.now().isoformat()),
            )
            return {"ok": True, "free": True, "amount": 0}

        if row[1] >= amount:
            conn.execute(
                "UPDATE user_credits SET balance = balance - ?, total_changed = total_changed + ?, updated_at = ? WHERE user_id = ?",
                (amount, amount, datetime.now().isoformat(), user_id),
            )
            conn.execute(
                "INSERT INTO credit_transactions (user_id, amount, tx_type, description, created_at) VALUES (?, ?, 'deduct', ?, ?)",
                (user_id, -amount, "心理模拟", datetime.now().isoformat()),
            )
            return {"ok": True, "free": False, "amount": amount}

        return {"ok": False, "error": f"余额不足，需要 ¥{amount:.2f}，当前 ¥{row[1]:.2f}"}

def add_credits(user_id: str, amount: float, description: str = "充值") -> bool:
    """添加信用额度"""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "UPDATE user_credits SET balance = balance + ?, total_changed = total_changed + ?, updated_at = ? WHERE user_id = ?",
                (amount, amount, datetime.now().isoformat(), user_id),
            )
            conn.execute(
                "INSERT INTO credit_transactions (user_id, amount, tx_type, description, created_at) VALUES (?, ?, 'recharge', ?, ?)",
                (user_id, amount, description, datetime.now().isoformat()),
            )
        return True
    except Exception as e:
        logger.error(f"Add credits failed: {e}")
        return False

def get_transactions(user_id: str, limit: int = 20) -> list[dict]:
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM credit_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
