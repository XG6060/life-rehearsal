"""人格测评 — 12 题 BigFive 大五人格问卷

每维度 2-3 题，7 点李克特量表 (1=非常不同意 ~ 7=非常同意)。
部分题目反向计分。返回 BigFive 模型（各维度 0-1）。
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models.user import BigFive


@dataclass
class QuizQuestion:
    """一道测评题目"""
    id: int
    dimension: str  # O / C / E / A / N
    text: str
    reverse: bool = False  # 是否反向计分


# ── 12 道题目 ────────────────────────────────────────────────────
_QUESTIONS: list[QuizQuestion] = [
    # 开放性 Openness (3 题)
    QuizQuestion(1, "O", "我喜欢尝试新的做事方式，即使结果不确定"),
    QuizQuestion(2, "O", "我对艺术、音乐或文学有强烈的感受力"),
    QuizQuestion(3, "O", "我倾向于遵循已经验证的方法，而不是去试验新的", reverse=True),
    # 尽责性 Conscientiousness (2 题)
    QuizQuestion(4, "C", "我做决定前会仔细权衡所有选项"),
    QuizQuestion(5, "C", "我通常会提前计划，而不是临时应对"),
    # 外向性 Extraversion (2 题)
    QuizQuestion(6, "E", "在做重要决定时，我倾向于和他人讨论交流"),
    QuizQuestion(7, "E", "遇到问题时，我更喜欢独自思考而不是向别人倾诉", reverse=True),
    # 宜人性 Agreeableness (2 题)
    QuizQuestion(8, "A", "做决定时，我会优先考虑对身边人的影响"),
    QuizQuestion(9, "A", "我认为自己的需求比别人的感受更重要", reverse=True),
    # 神经质 Neuroticism (3 题)
    QuizQuestion(10, "N", "面对不确定性时，我很容易感到焦虑"),
    QuizQuestion(11, "N", "我常常反复回想过去的错误决定"),
    QuizQuestion(12, "N", "重大决定之后，我一般不会怀疑自己的选择", reverse=True),
]

# 维度映射到 BigFive 字段名
_DIMENSION_FIELDS = {
    "O": "openness",
    "C": "conscientiousness",
    "E": "extraversion",
    "A": "agreeableness",
    "N": "neuroticism",
}


def get_questions() -> list[QuizQuestion]:
    """获取所有题目"""
    return list(_QUESTIONS)


def score(answers: list[int]) -> BigFive:
    """将 12 题的原始分数（1-7）转换为 BigFive 模型

    Args:
        answers: 长度为 12 的列表，每个元素为 1-7 的整数

    Returns:
        BigFive — 各维度 0-1

    Raises:
        ValueError: 答案数量或范围不正确
    """
    if len(answers) != 12:
        raise ValueError(f"需要 12 个答案，收到 {len(answers)} 个")
    if any(a < 1 or a > 7 for a in answers):
        raise ValueError("答案必须在 1-7 范围内")

    # 按维度分组分数
    dim_scores: dict[str, list[float]] = {d: [] for d in _DIMENSION_FIELDS}

    for i, q in enumerate(_QUESTIONS):
        raw = answers[i]
        # 映射到 0-1
        if q.reverse:
            normalized = (7 - raw) / 6.0  # 反向：答 1 → 1.0, 答 7 → 0.0
        else:
            normalized = (raw - 1) / 6.0  # 正向：答 1 → 0.0, 答 7 → 1.0
        dim_scores[q.dimension].append(normalized)

    # 计算各维度平均分
    kwargs = {}
    for dim, field in _DIMENSION_FIELDS.items():
        scores = dim_scores[dim]
        kwargs[field] = round(sum(scores) / len(scores), 3)

    return BigFive(**kwargs)
