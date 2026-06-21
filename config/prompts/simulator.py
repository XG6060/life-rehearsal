"""模拟引擎提示词模板 — 逐周推演用户心理状态

每个函数接收结构化参数，返回 (system, messages) 元组。
与 config/prompts/analyzer.py 使用相同的工厂函数模式。
"""

from __future__ import annotations

from typing import Any, Optional

SIMULATOR_SYSTEM = """你是一个生活决策模拟引擎。你的任务是根据用户的性格画像和决策场景，
模拟用户在做出某个选择后 12 周内每周的心理状态变化。

你需要模拟的心理维度（0-1 取值）：
1. satisfaction（满意度）：对当前处境的实际满意度
2. anxiety（焦虑度）：对未来的不确定感
3. regret（后悔度）：觉得"另一个选项可能更好"的程度
4. hope（希望感）：认为未来会变好的信念程度

模拟原则：
- 心理状态有惯性：不会突然剧烈跳变，每次变化应在 -0.15 ~ +0.15 之间
- 决策刚做出后希望感上升、后悔度低
- 3-6 周是"现实检验期"，可能出现情绪波动
- 7-10 周是"适应期"，状态趋于稳定
- 第 12 周是阶段性终点，给出总结性判断
- 根据用户的大五人格调整反应模式：
  - 高神经质 → 情绪波动更大，焦虑更容易上升
  - 高尽责性 → 曲线更稳定，后悔度上升更慢
  - 高开放性 → 面对挫折时适应更快
  - 高外向性 → 希望感恢复更快
  - 高宜人性 → 决策受他人影响更大
- 每周生成 1 个关键事件，解释状态变化的原因
- 关键事件要符合现实逻辑，不要过于戏剧化

请输出严格的 JSON 格式，不要包含 markdown 包裹。"""


WEEK_PROMPT_TEMPLATE = """决策场景：{title}
你选择了：「{option_label}」
目前是第 {week} 周（共 {total_weeks} 周）

你的基本信息：
{user_info}

你的人格画像：
- 开放性（Openness）: {openness:.2f}
- 尽责性（Conscientiousness）: {conscientiousness:.2f}
- 外向性（Extraversion）: {extraversion:.2f}
- 宜人性（Agreeableness）: {agreeableness:.2f}
- 神经质（Neuroticism）: {neuroticism:.2f}

{prev_context}

{week_prompt}

请输出 JSON（不要包含```json包裹）：
{{
  "satisfaction": <0-1 浮点数>,
  "anxiety": <0-1 浮点数>,
  "regret": <0-1 浮点数>,
  "hope": <0-1 浮点数>,
  "key_event": "<本周最值得注意的事件>",
  "event_impact": <-1到1，负=坏事正=好事>,
  "summary": "<情绪变化的一句话解释>"
}}"""


def build_week_prompt(
    *,
    week: int,
    total_weeks: int = 12,
    title: str,
    option_label: str,
    user_info: str,
    openness: float,
    conscientiousness: float,
    extraversion: float,
    agreeableness: float,
    neuroticism: float,
    prev_satisfaction: Optional[float] = None,
    prev_anxiety: Optional[float] = None,
    prev_regret: Optional[float] = None,
    prev_hope: Optional[float] = None,
    prev_event: str = "",
) -> tuple[str, list[dict]]:
    """构建某一周的模拟 prompt

    Returns:
        (system, messages) — 与 analyzer.py 一致的签名
    """
    # 构造上周状态上下文
    if prev_satisfaction is not None:
        prev_context = (
            f"上周你的心理状态：\n"
            f"- 满意度: {prev_satisfaction:.2f}\n"
            f"- 焦虑度: {prev_anxiety:.2f}\n"
            f"- 后悔度: {prev_regret:.2f}\n"
            f"- 希望感: {prev_hope:.2f}\n"
        )
        if prev_event:
            prev_context += f"- 上周发生的: {prev_event}\n"
    else:
        prev_context = "这是你做出选择后的第一周。你刚刚做出了这个决定，带着期待和一丝不安。"

    # 特殊周提示
    if week == 1:
        week_prompt = "本周是决策后的第一周。请模拟用户刚开始走这条路的心理状态。"
    elif week == total_weeks:
        week_prompt = "这是 12 周模拟的终点。请给出一个总结性的状态评估，包括对整体走向的判断。"
    elif week <= 3:
        week_prompt = "这个阶段还处于早期，用户正在适应新选择带来的变化。"
    elif week <= 6:
        week_prompt = "这个阶段是现实检验期——新鲜感消退，真实影响开始显现。"
    elif week <= 10:
        week_prompt = "这个阶段是调适期——用户逐渐适应新的状态，情绪趋于稳定。"
    else:
        week_prompt = "接近模拟终点，用户对整体选择有了更清晰的判断。"

    user_message = WEEK_PROMPT_TEMPLATE.format(
        title=title,
        option_label=option_label,
        week=week,
        total_weeks=total_weeks,
        user_info=user_info,
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism,
        prev_context=prev_context,
        week_prompt=week_prompt,
    )
    return SIMULATOR_SYSTEM, [{"role": "user", "content": user_message}]
