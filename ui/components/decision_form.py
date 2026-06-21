"""决策输入表单组件"""

from __future__ import annotations

from typing import Optional

import streamlit as st


def render_quick_scenario_selector() -> Optional[str]:
    """快速场景选择器"""
    scenarios = {
        "": None,
        "💼 要不要辞职/换工作": "career",
        "💔 要不要分手": "relationship",
        "🏠 要不要搬家/换城市": "relocation",
        "📚 要不要考研/留学": "education",
    }

    selected = st.selectbox(
        "选择一个常见场景（可选）",
        options=list(scenarios.keys()),
        index=0,
    )

    return scenarios.get(selected)


def render_context_guide() -> None:
    """显示输入引导"""
    st.markdown(
        "**建议包含：**\n"
        "- **现状**：现在的情况\n"
        "- **纠结**：你在哪几个选项之间犹豫\n"
        "- **担心**：你最担心什么\n"
        "- **期望**：你希望通过这个决定得到什么",
    )


def render_category_selector() -> str:
    """决策类别选择器"""
    return st.selectbox(
        "**类别**",
        options=["职业", "感情", "搬家", "求学", "家庭", "其他"],
        index=0,
    )


def render_user_background() -> tuple[str, str, str]:
    """用户背景信息输入（匿名）"""
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.selectbox(
            "年龄段",
            options=["", "18岁以下", "18-24", "25-30", "31-35", "36-40", "40以上"],
            index=0,
        )
    with col2:
        occupation = st.text_input("职业（选填）", placeholder="如：互联网/IT")
    with col3:
        city = st.text_input("城市（选填）", placeholder="如：一线城市")
    return age, occupation, city
