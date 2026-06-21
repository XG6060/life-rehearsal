"""Token 用量统计"""

from src.llm.client import get_llm_client


def get_token_stats() -> dict:
    """获取全局 Token 使用统计"""
    return get_llm_client().get_stats()


def get_session_token_usage() -> int:
    """获取当前会话的 Token 使用量"""
    return get_llm_client().budget.used_in_session


def budget_remaining() -> int:
    """获取剩余 Token 预算"""
    return get_llm_client().budget.session_remaining
