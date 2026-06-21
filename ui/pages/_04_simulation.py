"""模拟预演页面 — 人格测评 → 启动模拟 → 结果展示

四个阶段（由 st.session_state.simulation_phase 控制）：
  1. quiz — 12 题人格测评
  2. ready — 显示画像 + 启动按钮
  3. running — 进度显示
  4. completed — 曲线对比 + 关键事件
"""

from __future__ import annotations

import threading

import streamlit as st

# 导出函数列表（供 app.py 使用）
_EXPORTED_FUNCS = ["check_sim_result", "reset_all_sim_state"]
import plotly.express as px
import pandas as pd

from src.core.simulator.personality_quiz import get_questions, score as score_quiz
from src.services.simulation_service import SimulationService
from src.db.history_store import HistoryStore
from src.models.decision import Decision
from src.models.simulation import EmotionalCurve

# ── 线程间通信（复用 _01_decision_input 的模式） ────────────────
_SIM_RESULT: dict = {}
_SIM_LOCK = threading.Lock()


def _init_session():
    if "simulation_phase" not in st.session_state:
        st.session_state.simulation_phase = "quiz"
    if "big_five" not in st.session_state:
        st.session_state.big_five = None
    if "sim_result" not in st.session_state:
        st.session_state.sim_result = None
    if "sim_quiz_answers" not in st.session_state:
        st.session_state.sim_quiz_answers = [4] * 12  # 默认中等
    if "sim_error" not in st.session_state:
        st.session_state.sim_error = None


def render() -> None:
    _init_session()

    # 查看历史模拟结果时跳过决策数据检查
    has_result = st.session_state.get("sim_result") is not None
    has_decision = st.session_state.get("last_decision_input") is not None
    if not has_decision and not has_result:
        st.markdown("# 模拟预演")
        st.warning(
            "还没有可用的决策数据。\n\n"
            "请先在「输入决策」页面提交一个决策分析，"
            "然后才能运行心理模拟。"
        )
        if st.button("去输入决策", use_container_width=True):
            st.session_state.page = "input"
            st.rerun()
        return

    phase = st.session_state.simulation_phase

    if phase == "quiz":
        _render_quiz()
    elif phase == "ready":
        _render_ready()
    elif phase == "running":
        _render_running()
    elif phase == "completed":
        _render_completed()
    else:
        st.error(f"未知阶段: {phase}")


# ═══════════════════════════════════════════════════════════════════
# 阶段 1：人格测评
# ═══════════════════════════════════════════════════════════════════

def _render_quiz():
    st.markdown("# 人格测评")
    st.markdown(
        "在运行模拟之前，先了解一下你的性格特点。"
        "这将帮助 AI 更准确地预测你在不同选择下的心理变化。"
    )
    st.markdown("请根据你的真实感受，对以下描述进行评分：")
    st.caption("1 = 非常不同意　→→→　7 = 非常同意")

    st.markdown("---")

    questions = get_questions()
    answers = st.session_state.sim_quiz_answers

    for i, q in enumerate(questions):
        label = f"**{q.id}. {q.text}**"
        dim_name = {"O": "开放性", "C": "尽责性", "E": "外向性",
                     "A": "宜人性", "N": "神经质"}.get(q.dimension, q.dimension)
        st.caption(f"维度：{dim_name}")
        answers[i] = st.slider(
            label,
            min_value=1, max_value=7, value=answers[i],
            key=f"quiz_q_{q.id}",
        )

    st.markdown("---")

    if st.button("计算我的画像", type="primary", use_container_width=True):
        try:
            big_five = score_quiz(answers)
            st.session_state.big_five = big_five
            st.session_state.simulation_phase = "ready"
            st.rerun()
        except ValueError as e:
            st.error(str(e))


# ═══════════════════════════════════════════════════════════════════
# 阶段 2：就绪
# ═══════════════════════════════════════════════════════════════════

def _render_ready():
    st.markdown("# 准备模拟")
    bf = st.session_state.big_five
    _render_bigfive_chart(bf)

    # ── 获取所有选项标签 ──────────────────────────────────────────
    decision_input = st.session_state.get("last_decision_input")
    labels = _resolve_option_labels(decision_input)
    title = getattr(decision_input, "title", "未命名决策") if decision_input else "未命名决策"

    st.markdown(f"**决策问题：** {title}")
    st.markdown("---")
    st.markdown(f"### 即将模拟的选项（共 {len(labels)} 个）")

    # 动态渲染 N 个选项卡片
    cols = st.columns(min(len(labels), 4))
    for i, label in enumerate(labels):
        with cols[i % len(cols)]:
            st.info(f"**{label}**")
            st.caption(f"模拟选择这条路 12 周的心理变化")

    st.markdown("---")
    total_calls = len(labels) * 12
    st.markdown(
        f"将对 **{len(labels)}** 个选项逐周推演，共约 **{total_calls}** 次分析，"
        "期间你可以自由切换到其他页面。"
    )

    if st.button("开始模拟", type="primary", use_container_width=True):
        _start_simulation()
        st.rerun()

    if st.button("重新测评", use_container_width=True):
        st.session_state.simulation_phase = "quiz"
        st.session_state.big_five = None
        st.rerun()


def _render_bigfive_chart(bf):
    """渲染 BigFive 雷达图"""
    labels = ["开放性", "尽责性", "外向性", "宜人性", "神经质"]
    values = [bf.openness, bf.conscientiousness, bf.extraversion,
              bf.agreeableness, bf.neuroticism]

    df = pd.DataFrame({
        "维度": labels + labels[:1],
        "分数": values + values[:1],
    })
    fig = px.line_polar(
        df, r="分数", theta="维度", line_close=True,
        range_r=[0, 1], title="",
    )
    fig.update_traces(fill="toself", line_color="#4A90D9", hoverinfo="skip")
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        dragmode=False,
        hovermode=False,
    )
    fig.update_polars(
        radialaxis=dict(visible=False),
        angularaxis=dict(tickfont=dict(size=14)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 数值说明
    st.markdown("---")
    st.markdown("**各维度说明：**")
    dims = [
        ("开放性", bf.openness, "对新事物的接受度", "保守务实", "开放好奇"),
        ("尽责性", bf.conscientiousness, "自律和规划倾向", "随性灵活", "周密有条理"),
        ("外向性", bf.extraversion, "从外界获取能量的程度", "内向独处", "外向活跃"),
        ("宜人性", bf.agreeableness, "在决策中考虑他人的程度", "以己为先", "友善随和"),
        ("神经质", bf.neuroticism, "情绪敏感度和稳定性", "情绪稳定", "容易焦虑"),
    ]
    for icon_label, val, desc, low_label, high_label in dims:
        pct = int(val * 100)
        st.markdown(f"**{icon_label}**: {pct}分 — {desc}")
        st.caption(f"你偏向「{low_label}」←{'─' * 20}→「{high_label}」")
        st.progress(val, text=f"{pct}/100")


# ═══════════════════════════════════════════════════════════════════
# 阶段 3：运行中
# ═══════════════════════════════════════════════════════════════════

def _render_running():
    st.markdown("# 模拟运行中")
    st.info(
        "AI 正在逐周推演你的心理状态变化。"
        "你可以切换到其他页面浏览，模拟完成后顶部会有通知。"
    )

    with _SIM_LOCK:
        weeks = _SIM_RESULT.get("weeks", {})

    for i in range(st.session_state.get("_sim_count", 0)):
        label = st.session_state.get(f"_sim_label_{i}", f"选项 {i + 1}")
        week = weeks.get(i, 0)
        total = 12
        pct = week / total
        st.markdown(f"**{label}**")
        st.progress(pct, text=f"{week} / {total} 周")

    st.caption("模拟完成后顶部会自动出现通知。")


# ═══════════════════════════════════════════════════════════════════
# 阶段 4：结果展示
# ═══════════════════════════════════════════════════════════════════

def _render_comparison_summary(curves, labels):
    """生成 N 条路径的对比总结"""
    if not curves or len(curves) < 2:
        return

    st.markdown("### 对比总结")
    lines = []

    # 终周满意度对比
    end_sats = [(c.satisfaction[-1] if c.satisfaction else 0, labels[i]) for i, c in enumerate(curves)]
    end_sats.sort(reverse=True)
    best_sat, best_label = end_sats[0]
    worst_sat, worst_label = end_sats[-1]
    if best_sat - worst_sat > 0.1:
        lines.append(f"😊 **满意度最高**：{best_label}（终周 {best_sat:.0%}），**最低**：{worst_label}（{worst_sat:.0%}）")
    else:
        lines.append(f"😐 **满意度**：各选项终周满意度接近（{best_sat:.0%} ~ {worst_sat:.0%}）")

    # 后悔峰值对比
    peak_regrets = [(max(c.regret) if c.regret else 0, labels[i]) for i, c in enumerate(curves)]
    peak_regrets.sort()
    lowest_reg, low_label = peak_regrets[0]
    highest_reg, high_label = peak_regrets[-1]
    if highest_reg - lowest_reg > 0.1:
        lines.append(f"😖 **后悔风险最低**：{low_label}（峰值 {lowest_reg:.0%}），**最高**：{high_label}（{highest_reg:.0%}）")

    # 周均焦虑对比
    avg_anxieties = [
        (sum(c.anxiety) / len(c.anxiety) if c.anxiety else 0, labels[i])
        for i, c in enumerate(curves)
    ]
    avg_anxieties.sort()
    calmest_label = avg_anxieties[0][1]
    most_anxious_label = avg_anxieties[-1][1]
    if avg_anxieties[-1][0] - avg_anxieties[0][0] > 0.05:
        lines.append(f"😰 **最平静**：{calmest_label}，**最焦虑**：{most_anxious_label}")

    for line in lines:
        st.markdown(line)


def _render_completed():
    st.markdown("# 模拟结果")
    result = st.session_state.sim_result

    if result is None:
        st.error("模拟结果加载失败。")
        return

    curves = result.get("curves", [])
    labels = result.get("labels", [])
    timing_ms = result.get("timing_ms", 0)

    if not curves:
        st.error("模拟数据为空。")
        return

    n = len(curves)
    st.markdown(f"共模拟 **{n}** 个选项，耗时 **{timing_ms / 1000:.1f}s**")

    # 摘要指标
    metrics_cols = st.columns(min(n, 5))
    for i in range(n):
        with metrics_cols[i % len(metrics_cols)]:
            c = curves[i]
            label = labels[i] if i < len(labels) else f"选项 {i + 1}"
            last_sat = c.satisfaction[-1] if c.satisfaction else 0
            peak_reg = max(c.regret) if c.regret else 0
            st.metric(f"📈 终周满意度 ({label})", f"{last_sat:.0%}")
            st.metric(f"😖 最高后悔度 ({label})", f"{peak_reg:.0%}")

    # 对比总结
    st.markdown("---")
    if n >= 2:
        _render_comparison_summary(curves, labels)

    # 叠加对比图
    from ui.components.emotional_chart import render_comparison_chart, render_emotional_curve

    st.markdown("### 各选项心理状态叠加对比")
    fig_overlay = render_comparison_chart(curves, labels)
    st.plotly_chart(fig_overlay, use_container_width=True)

    # 各自曲线（N 个 tab）
    if n >= 2:
        st.markdown("---")
        st.markdown("### 📈 各选项详细曲线")
        tabs = st.tabs([labels[i] if i < len(labels) else f"选项 {i + 1}" for i in range(n)])
        for i in range(n):
            with tabs[i]:
                fig = render_emotional_curve(curves[i])
                st.plotly_chart(fig, use_container_width=True)

    # 关键事件表格
    if n >= 2:
        st.markdown("---")
        st.markdown("### 🔑 关键事件")

        event_cols = st.columns(min(n, 4))
        for i in range(n):
            with event_cols[i % len(event_cols)]:
                label = labels[i] if i < len(labels) else f"选项 {i + 1}"
                st.markdown(f"**{label}**")
                events = [
                    {"周": m.week, "事件": m.description, "类型": _moment_label(m.moment_type)}
                    for m in curves[i].key_moments
                ] if curves[i].key_moments else []
                if events:
                    st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
                else:
                    st.caption("无特殊事件")

    # 重新开始
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("重新模拟", use_container_width=True):
            _reset_simulation()
            st.rerun()
    with col2:
        if st.button("回到输入决策", use_container_width=True):
            st.session_state.page = "input"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
# 后台线程：启动模拟
# ═══════════════════════════════════════════════════════════════════

def _start_simulation():
    """在后台线程启动模拟（支持 N 个选项）"""
    global _SIM_RESULT
    decision_input = st.session_state.get("last_decision_input")
    big_five = st.session_state.big_five

    if not decision_input:
        st.error("没有可用的决策分析数据，请先在输入决策页面提交分析。")
        return

    # 构建 Decision 对象
    from src.models.decision import Decision
    decision = Decision(
        title=getattr(decision_input, "title", ""),
        category=getattr(decision_input, "category", "other"),
        context=getattr(decision_input, "context", ""),
        age_range=getattr(decision_input, "age_range", ""),
        occupation_category=getattr(decision_input, "occupation_category", ""),
        city_tier=getattr(decision_input, "city_tier", ""),
    )

    # 从分析报告中取 LLM 提取的选项标签
    labels = _resolve_option_labels(decision_input)

    # 存储到 session_state 供进度条读取
    st.session_state._sim_count = len(labels)
    for i, label in enumerate(labels):
        st.session_state[f"_sim_label_{i}"] = label
    st.session_state.simulation_phase = "running"

    _SIM_RESULT = {"weeks": {i: 0 for i in range(len(labels))}}

    def _run():
        global _SIM_RESULT
        try:
            service = SimulationService()
            result = service.run(
                decision=decision,
                big_five=big_five,
                option_labels=labels,
            )

            # 包装结果 dict（用 list 替代 curve_a/curve_b）
            result_data = {
                "curves": result.curves,
                "labels": result.option_labels,
                "big_five": result.big_five,
                "decision_title": result.decision_title,
                "timing_ms": result.timing_ms,
                "status": result.status.value,
            }
            with _SIM_LOCK:
                _SIM_RESULT = result_data
                _SIM_RESULT["ready"] = True

        except Exception as e:
            with _SIM_LOCK:
                _SIM_RESULT = {"ready": True, "error": str(e)}

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def check_sim_result():
    """主线程调用：检查模拟结果（由 app.py 的 fragment 驱动）"""
    global _SIM_RESULT
    with _SIM_LOCK:
        if not _SIM_RESULT.get("ready"):
            return False

        if "error" in _SIM_RESULT:
            st.session_state.sim_error = _SIM_RESULT["error"]
            st.session_state.simulation_phase = "completed"
            st.session_state.sim_result = None
        else:
            st.session_state.sim_result = {
                "curves": _SIM_RESULT.get("curves", []),
                "labels": _SIM_RESULT.get("labels", []),
                "big_five": _SIM_RESULT.get("big_five"),
                "timing_ms": _SIM_RESULT.get("timing_ms", 0),
            }
            st.session_state.simulation_phase = "completed"
            st.session_state.pop("_sim_from_history", None)

            # 保存到历史记录（所有曲线一起存）
            try:
                from streamlit.runtime.scriptrunner import get_script_run_ctx
                _uid = st.session_state.get("logged_in_user", {}).get("id", "")
                store = HistoryStore()
                curves = _SIM_RESULT.get("curves", [])
                labels = _SIM_RESULT.get("labels", [])
                bf_obj = _SIM_RESULT.get("big_five")
                if curves and bf_obj:
                    store.save_simulation(
                        decision_title=_SIM_RESULT.get("decision_title", ""),
                        big_five_json=bf_obj.model_dump_json(),
                        curves=curves,
                        labels=labels,
                        timing_ms=_SIM_RESULT.get("timing_ms", 0),
                        user_id=_uid,
                    )
            except Exception as e:
                pass

        _SIM_RESULT = {}
        return True


def reset_all_sim_state():
    """清除所有模拟相关的 session state（供 app.py 调用）"""
    st.session_state.simulation_phase = "quiz"
    st.session_state.big_five = None
    st.session_state.sim_result = None
    st.session_state.sim_error = None
    st.session_state._sim_count = 0
    for k in list(st.session_state.keys()):
        if k.startswith("_sim_label_") or k in ("_sim_label_a", "_sim_label_b"):
            del st.session_state[k]
    global _SIM_RESULT
    _SIM_RESULT = {}


def _reset_simulation():
    """重置模拟状态"""
    reset_all_sim_state()


# ═══════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════

def _resolve_option_labels(decision_input) -> list[str]:
    """从分析结果中提取所有选项标签，返回列表

    优先级：
    1. LLM 从描述中提取的选项（scenario_analyses）
    2. 用户手动填写的补充选项
    3. 兜底：["选项 A", "选项 B"]
    """
    # 最高优先级：LLM 从描述中提取的选项
    last_result = st.session_state.get("last_result")
    if last_result and last_result.report.scenario_analyses:
        labels = [a.option_label for a in last_result.report.scenario_analyses]
        if labels:
            return labels

    # 次优：用户手动填写的选项
    if decision_input:
        raw_opts = getattr(decision_input, "options", []) or []
        labels = [o.get("label", "") for o in raw_opts if o.get("label")]
        if labels:
            return labels

    # 兜底
    return ["选项 A", "选项 B"]

def _argmax(lst: list[float]) -> int:
    """返回列表中最大值的索引"""
    if not lst:
        return -1
    return max(range(len(lst)), key=lambda i: lst[i])


def _moment_label(t: str) -> str:
    labels = {
        "milestone": "📌 里程碑",
        "regret_peak": "😖 后悔峰值",
        "crisis": "💢 情绪低谷",
        "breakthrough": "🌟 转机",
        "confidence_peak": "💪 信心高峰",
    }
    return labels.get(t, t)
