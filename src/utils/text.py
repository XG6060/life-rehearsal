"""文本处理工具函数"""

import re
from typing import Any


def truncate(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """截断文本到指定长度，保留完整句子"""
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    # 尽量在句子边界截断
    last_period = max(
        truncated.rfind("。"), truncated.rfind("."),
        truncated.rfind("！"), truncated.rfind("？"),
        truncated.rfind("\n"),
    )
    if last_period > max_length * 0.8:
        return truncated[: last_period + 1] + suffix
    return truncated + suffix


def extract_key_sentences(text: str, max_sentences: int = 5) -> list[str]:
    """提取文本中最关键的前 N 个句子"""
    # 按中文/英文句号分割
    sentences = re.split(r"[。！？.!?\n]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    return sentences[:max_sentences]


def count_characters(text: str) -> dict[str, int]:
    """统计文本中的中文字符、英文字母、数字、标点等数量"""
    stats: dict[str, int] = {
        "chinese": 0,
        "english": 0,
        "digits": 0,
        "punctuation": 0,
        "total": len(text),
    }
    for char in text:
        if "一" <= char <= "鿿":
            stats["chinese"] += 1
        elif char.isalpha():
            stats["english"] += 1
        elif char.isdigit():
            stats["digits"] += 1
        else:
            stats["punctuation"] += 1
    return stats


def safe_json_parse(text: str) -> dict[str, Any] | None:
    """从 LLM 输出中安全提取 JSON（处理 markdown 包裹等问题）"""
    import json

    # 尝试提取 ```json 块
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    # 尝试解析
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试修复常见问题
    try:
        # 移除注释
        cleaned = re.sub(r"//.*?\n", "\n", text)
        # 移除尾部逗号
        cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
