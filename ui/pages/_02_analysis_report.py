"""分析报告展示页面 — 显示上次分析结果，或提示'还未进行过分析'"""

from __future__ import annotations

import streamlit as st

from src.core.report.visualizer import Visualizer


def render() -> None:
    """渲染分析报告页面"""
    result = st.session_state.get("last_result")

    # ── 从未分析过 ─────────────────────────────────────────────────
    if result is None:
        running = st.session_state.get("analysis_running", False)
        if running:
            st.info("后台分析正在进行中，完成后会通知你。")
        else:
            st.info("还未进行过分析，请先在「输入决策」页面提交你的决策。")
        return

    report = result.report

    # ── 顶部摘要 ───────────────────────────────────────────────────
    st.markdown("# 📊 决策分析报告")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("发现的偏误", report.bias_count)
    with col2:
        st.metric("追问数量", len(report.questions))
    with col3:
        style_name = report.decision_style.style if report.decision_style else "待分析"
        st.metric("决策风格", style_name)
    with col4:
        st.metric("分析耗时", f"{result.timing_ms / 1000:.1f}s")

    st.markdown("---")

    # ── 核心洞察 ───────────────────────────────────────────────────
    st.markdown("## 核心洞察")
    if report.key_insight:
        st.info(report.key_insight)
    else:
        st.caption("暂未生成核心洞察")

    # ── 叙事化报告 ──────────────────────────────────────────────────
    if result.narrative_text:
        st.markdown("## 完整分析")
        st.markdown(result.narrative_text)
    else:
        st.caption("暂未生成长篇分析")

    # ── 认知偏误 ───────────────────────────────────────────────────
    if report.biases:
        st.markdown("---")
        st.markdown("## 认知偏误检测")

        viz = Visualizer()
        radar_data = viz.bias_radar_data(report)
        if radar_data["labels"]:
            import plotly.express as px
            import pandas as pd
            df = pd.DataFrame({
                "偏误类型": radar_data["labels"],
                "严重程度": radar_data["values"],
            })
            fig = px.bar(
                df, x="偏误类型", y="严重程度",
                title="认知偏误严重程度", color="严重程度",
                color_continuous_scale="Reds", range_y=[0, 100],
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        for i, bias in enumerate(report.biases):
            with st.expander(
                f"{'' if bias.severity > 0.6 else ''} "
                f"{bias.bias_name_cn} (严重度: {bias.severity:.0%})",
                expanded=i == 0,
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**证据**")
                    st.markdown(f"> \"{bias.evidence}\"")
                with col2:
                    st.markdown("**建议**")
                    st.markdown(bias.suggestion)
                st.markdown("**解析**")
                st.markdown(bias.explanation)

    # ── 决策风格 ───────────────────────────────────────────────────
    if report.decision_style:
        st.markdown("---")
        st.markdown("## 你的决策风格")
        style = report.decision_style
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{style.style_description}**")
            if style.strengths:
                st.markdown("**优势：**")
                for s in style.strengths:
                    st.markdown(f"- {s}")
        with col2:
            if style.blind_spots:
                st.markdown("**盲区：**")
                for b in style.blind_spots:
                    st.markdown(f"- {b}")
        if style.advice:
            st.markdown(f"**建议：** {style.advice}")

    # ── 追问 ───────────────────────────────────────────────────────
    if report.questions:
        st.markdown("---")
        st.markdown("## 值得追问自己的问题")
        categories = {
            "clarify": ("🔍", "澄清类"), "challenge": ("⚡", "挑战类"),
            "perspective": ("👀", "换位思考"), "deepen": ("🌊", "深层需求"),
        }
        for q in report.questions:
            icon, label = categories.get(q.category, ("❓", "其他"))
            with st.container(border=True):
                st.markdown(f"**{icon} {q.question}**")
                st.caption(f"类别: {label} · {q.reason}")

    # ── 各选项分析 ─────────────────────────────────────────────────
    if report.scenario_analyses:
        st.markdown("---")
        st.markdown("## 各选项分析")
        tabs = st.tabs([s.option_label for s in report.scenario_analyses])
        for i, (tab, scenario) in enumerate(zip(tabs, report.scenario_analyses)):
            with tab:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**可能的机会**")
                    for opp in scenario.key_opportunities:
                        st.markdown(f"- {opp}")
                    if scenario.best_case:
                        st.markdown(f"\n**最好的情况：** {scenario.best_case}")
                with col2:
                    st.markdown("**可能的风险**")
                    for risk in scenario.key_risks:
                        st.markdown(f"- {risk}")
                    if scenario.worst_case:
                        st.markdown(f"\n**最坏的情况：** {scenario.worst_case}")
                if scenario.emotional_trajectory:
                    st.markdown(f"\n**心理轨迹预测：** {scenario.emotional_trajectory}")
                if scenario.regret_warning:
                    st.warning(f"{scenario.regret_warning}")

    # ── 模拟入口 ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 预演接下来会发生什么")
    st.markdown(
        "想知道选择不同选项后你的心理状态会如何变化吗？"
        "AI 会基于你的人格特征，模拟 12 周内你在两条路径上的心理轨迹。"
    )
    if st.button(f"运行心理模拟", use_container_width=True, type="primary"):
        st.session_state.page = "simulation"
        st.session_state.simulation_phase = "quiz"
        st.session_state.big_five = None
        st.session_state.sim_result = None
        st.rerun()

    # ── 底部 ──────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        f"分析时间: {report.created_at.strftime('%Y-%m-%d %H:%M')} | "
        f"模型: {report.llm_model_used or '未记录'} | "
        f"以上分析基于 AI 生成，仅供参考，不构成决策建议"
    )
