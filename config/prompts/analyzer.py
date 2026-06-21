"""决策分析提示词模板 — 所有面向 LLM 的提示词集中管理

每个函数接收格式化参数，返回完整的 system/user prompt。
使用中文提示词，确保对 Claude 的意图表达清晰。
"""

from __future__ import annotations

import json
from typing import Any


def _user_info_str(age_range: str = "", occupation: str = "", city: str = "") -> str:
    """生成用户画像文本，嵌入 LLM 提示中让分析更具针对性。"""
    parts = []
    if age_range:
        parts.append(f"年龄阶段：{age_range}")
    if occupation:
        parts.append(f"职业领域：{occupation}")
    if city:
        parts.append(f"所在城市：{city}")
    return "，".join(parts) if parts else ""


# ══════════════════════════════════════════════════════════════════════
# 1. 决策树拆解
# ══════════════════════════════════════════════════════════════════════

DECONSTRUCTOR_SYSTEM = """你是一个专业的决策分析师。你的任务是将用户描述的决策困境拆解为清晰的结构化决策树。

你需要分析：
1. 核心决策问题是什么
2. 用户面前有哪些可行的选项
3. 每个选项的优缺点
4. 影响决策的关键变量/因素
5. 用户叙述中隐含的假设
6. 用户所处的年龄段、职业和城市类型如何影响各选项的可行性

请输出严格的 JSON 格式，不要包含 markdown 包裹。
"""

DECONSTRUCTOR_USER_TEMPLATE = """请分析以下决策困境，输出 JSON 格式的决策树。

用户的决策问题：{title}
{user_info}
用户的详细描述：{context}

{options_hint}
{factors_hint}

请输出以下 JSON 格式（不要包含```json包裹）：
{{
    "root_question": "核心决策问题",
    "options": [
        {{"label": "选项A: xxx", "description": "详细描述", "pros": ["优点1", "优点2"], "cons": ["缺点1", "缺点2"]}},
        {{"label": "选项B: xxx", "description": "详细描述", "pros": ["优点1", "优点2"], "cons": ["缺点1", "缺点2"]}}
    ],
    "key_factors": [
        {{"name": "因素1", "importance": 0-1, "uncertainty": 0-1}}
    ],
    "assumptions": [
        "用户的隐含假设1",
        "用户的隐含假设2"
    ]
}}

注意：importance 和 uncertainty 使用 0-1 之间的浮点数。options 至少 2 个，最多 5 个。每个 option 的 pros 和 cons 各至少 1 条。"""


def build_deconstructor_prompt(
    title: str,
    context: str,
    options: list[dict[str, Any]] | None = None,
    factors: list[dict[str, Any]] | None = None,
    age_range: str = "",
    occupation: str = "",
    city: str = "",
) -> tuple[str, list[dict]]:
    """构建决策树拆解的 system 和 user prompt"""
    user_info = _user_info_str(age_range, occupation, city)
    options_hint = ""
    if options:
        options_hint = f"用户已经提出了一些选项：{json.dumps(options, ensure_ascii=False)}"
    else:
        options_hint = "请从用户的描述中自行提取存在的选项。"

    factors_hint = ""
    if factors:
        factors_hint = f"用户提到了这些关键因素：{json.dumps(factors, ensure_ascii=False)}"
    else:
        factors_hint = "请从用户的描述中提取影响决策的关键因素。"

    user_message = DECONSTRUCTOR_USER_TEMPLATE.format(
        title=title,
        user_info=user_info,
        context=context,
        options_hint=options_hint,
        factors_hint=factors_hint,
    )
    return DECONSTRUCTOR_SYSTEM, [{"role": "user", "content": user_message}]


# ══════════════════════════════════════════════════════════════════════
# 2. 认知偏误检测
# ══════════════════════════════════════════════════════════════════════

BIAS_DETECTOR_SYSTEM = """你是一个认知心理学家和行为经济学专家。你的任务是从用户的决策描述中识别出认知偏误。

你需要检测以下 6 种常见偏误：
1. 损失厌恶 — 是否过分夸大"失去"的痛苦，导致过于保守
2. 确认偏误 — 是否只寻找支持自己偏好的证据，忽视反面信息
3. 过度乐观 — 是否低估困难发生的概率和时间成本
4. 锚定效应 — 是否被某个数字、经历或他人的意见锚定
5. 现状偏好 — 是否仅仅因为"不想改变"而维持现状
6. 沉没成本 — 是否因为已经投入了时间/金钱/精力而难以放手

对每种被检测到的偏误，请给出用户原话中的具体证据。

请输出严格的 JSON 格式，不要包含 markdown 包裹。"""

BIAS_DETECTOR_USER_TEMPLATE = """请分析以下决策描述中存在的认知偏误。

决策问题：{title}
用户身份：{age_info}{occupation_info}{city_info}
用户决策风格（如已知）：{style_info}

用户的完整描述：
{context}

{options_context}

请分析上述描述中存在的认知偏误，输出 JSON 格式（不要包含```json包裹）：
{{
    "biases": [
        {{
            "bias_type": "loss_aversion / confirmation_bias / over_optimism / anchoring / status_quo / sunk_cost",
            "bias_name_cn": "偏误中文名称",
            "severity": 0-1之间的浮点数,
            "evidence": "用户原话中的具体证据（直接引用）",
            "explanation": "为什么这是偏误，心理学机制是什么",
            "suggestion": "如何纠正这个偏误的具体建议"
        }}
    ]
}}

注意：只列出确实存在的偏误，不存在的不列。severity 使用 0-1 之间的浮点数。每项 evidence 必须直接引用用户原话。"""


def build_bias_detector_prompt(
    title: str,
    context: str,
    options: list[dict[str, Any]] | None = None,
    age_range: str = "",
    occupation: str = "",
    city: str = "",
    style: str = "",
) -> tuple[str, list[dict]]:
    """构建偏误检测的 system 和 user prompt"""
    age_info = f"{age_range}岁，" if age_range else ""
    occupation_info = f"从事{occupation}，" if occupation else ""
    city_info = f"生活在{city}。" if city else ""
    style_info = style if style else "未知"

    options_context = ""
    if options:
        opts_str = "\n".join(
            f"  - {o.get('label', '')}: {o.get('description', '')}"
            for o in options
        )
        options_context = f"用户考虑的选项：\n{opts_str}"

    user_message = BIAS_DETECTOR_USER_TEMPLATE.format(
        title=title,
        context=context,
        age_info=age_info,
        occupation_info=occupation_info,
        city_info=city_info,
        style_info=style_info,
        options_context=options_context,
    )
    return BIAS_DETECTOR_SYSTEM, [{"role": "user", "content": user_message}]


# ══════════════════════════════════════════════════════════════════════
# 3. 决策风格分类
# ══════════════════════════════════════════════════════════════════════

STYLE_CLASSIFIER_SYSTEM = """你是一个决策心理学专家。请根据用户的决策描述，判断其决策风格类型。

类型说明：
- rational（理性分析型）：倾向于收集大量信息、列出利弊、做分析表格
- intuitive（直觉驱动型）：凭感觉做决定、相信第一印象、重视"心里舒服"
- dependent（依赖他人型）：反复征求他人意见、难以独自做决定、容易被影响
- avoidant（逃避型）：拖延做决定、希望问题自己消失、回避思考
- impulsive（冲动型）：一时兴起做决定、事后容易后悔、凭热情行动

分析时请注意：一个人可能混合多种风格，请判断最主导的那一种。

请输出严格的 JSON 格式。"""

STYLE_CLASSIFIER_USER_TEMPLATE = """请分析以下用户的决策风格。

决策问题：{title}
{user_info}
用户的描述：{context}

请输出 JSON 格式（不要包含```json包裹）：
{{
    "style": "rational / intuitive / dependent / avoidant / impulsive",
    "style_description": "这种风格的特点和表现（50字以内）",
    "strengths": ["优势1", "优势2"],
    "blind_spots": ["盲区1", "盲区2"],
    "advice": "针对该用户的决策建议"
}}"""


def build_style_classifier_prompt(
    title: str,
    context: str,
    age_range: str = "",
    occupation: str = "",
    city: str = "",
) -> tuple[str, list[dict]]:
    """构建决策风格分类的 system 和 user prompt"""
    user_info = _user_info_str(age_range, occupation, city)
    user_message = STYLE_CLASSIFIER_USER_TEMPLATE.format(
        title=title,
        user_info=user_info,
        context=context,
    )
    return STYLE_CLASSIFIER_SYSTEM, [{"role": "user", "content": user_message}]


# ══════════════════════════════════════════════════════════════════════
# 4. 苏格拉底式追问
# ══════════════════════════════════════════════════════════════════════

QUESTIONER_SYSTEM = """你是一个苏格拉底式的提问者。你的任务不是给建议，而是通过提问帮助用户自己理清思路。

你的问题应该覆盖以下维度：
1. 澄清（clarify）— 帮助用户提供更清晰的信息
2. 挑战（challenge）— 温和地质疑用户的假设
3. 换位思考（perspective）— 引导用户从不同角度思考
4. 深层需求（deepen）— 帮助用户触及真正的价值观和需求

每个问题应该：
- 具体而非泛泛（不要问"你考虑过其他选项吗"，要问"你说担心35岁危机，具体是担心什么"）
- 温和但有深度（不是尖锐的质问，而是真诚的好奇）
- 基于用户说过的具体内容

请输出严格的 JSON 格式。"""

QUESTIONER_USER_TEMPLATE = """根据以下用户信息，生成 4-6 个苏格拉底式追问，帮助用户深入思考自己的决策。

决策问题：{title}
{user_info}
用户的描述：{context}
{options_context}
{biases_context}

请输出 JSON 格式（不要包含```json包裹）：
{{
    "questions": [
        {{
            "question": "具体的追问内容",
            "category": "clarify / challenge / perspective / deepen",
            "reason": "为什么问这个问题"
        }}
    ]
}}

要求：生成 4-6 个问题，覆盖至少 3 种不同的类别。"""


def build_questioner_prompt(
    title: str,
    context: str,
    options: list[dict[str, Any]] | None = None,
    biases: list[str] | None = None,
    age_range: str = "",
    occupation: str = "",
    city: str = "",
) -> tuple[str, list[dict]]:
    """构建追问器的 system 和 user prompt"""
    user_info = _user_info_str(age_range, occupation, city)
    options_context = ""
    if options:
        opts_str = "\n".join(
            f"  - {o.get('label', '')}" for o in options
        )
        options_context = f"用户考虑的选项：\n{opts_str}"

    biases_context = ""
    if biases:
        biases_context = "检测到的认知偏误：\n" + "\n".join(f"  - {b}" for b in biases)

    user_message = QUESTIONER_USER_TEMPLATE.format(
        title=title,
        user_info=user_info,
        context=context,
        options_context=options_context,
        biases_context=biases_context,
    )
    return QUESTIONER_SYSTEM, [{"role": "user", "content": user_message}]


# ══════════════════════════════════════════════════════════════════════
# 5. 综合报告生成
# ══════════════════════════════════════════════════════════════════════

REPORT_BUILDER_SYSTEM = """你是一个决策报告撰写专家。请根据分析结果，生成一份清晰、有温度、可行动的决策分析报告。

报告风格要求：
- 专业但不冰冷：用通俗的语言解释专业概念
- 具体而不空泛：每个建议都要基于用户的具体情况
- 有温度：理解用户的纠结和焦虑，但不贩卖焦虑

请用中文输出纯文本（非 JSON），使用 markdown 格式。"""

REPORT_BUILDER_USER_TEMPLATE = """请根据以下分析数据，撰写一份完整的决策分析报告。

决策问题：{title}
{user_info}
决策树摘要：{tree_summary}

各选项分析：
{scenario_analyses}

检测到的认知偏误：
{bias_summary}

决策风格：{style_info}

追问问题：
{questions_summary}

请综合以上信息，写一份完整的决策分析报告。报告结构如下：

## 📋 核心洞察
（1-2句话点出最关键的信息）

## 🔀 你的选择分支
（简要概括每个选项的利弊和可能结果）

## 🧠 思维盲区
（列出检测到的认知偏误，解释为什么是偏误，如何避免，只说确实存在的）

## 💭 值得追问自己的问题
（列出最有价值的 3-5 个问题）

## 🎯 下一步行动建议
（具体可操作的 2-3 条建议）

风格要求：温暖、共情、专业。像是在和一个信任的朋友对话。"""


def build_report_prompt(
    title: str,
    tree_summary: str,
    scenario_analyses: str,
    bias_summary: str,
    style_info: str,
    questions_summary: str,
    age_range: str = "",
    occupation: str = "",
    city: str = "",
) -> tuple[str, list[dict]]:
    """构建报告生成的 system 和 user prompt"""
    user_info = _user_info_str(age_range, occupation, city)
    user_message = REPORT_BUILDER_USER_TEMPLATE.format(
        title=title,
        user_info=user_info,
        tree_summary=tree_summary,
        scenario_analyses=scenario_analyses,
        bias_summary=bias_summary,
        style_info=style_info,
        questions_summary=questions_summary,
    )
    return REPORT_BUILDER_SYSTEM, [{"role": "user", "content": user_message}]
