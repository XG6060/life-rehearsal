"""历史记录页面 — 展示所有历史分析记录，支持查看和删除"""

from __future__ import annotations

import streamlit as st

from src.db.history_store import HistoryStore

# 场景分类英文 → 中文映射
_CATEGORY_LABELS: dict[str, str] = {
    "career": "职业", "relationship": "感情", "relocation": "搬家",
    "education": "求学", "family": "家庭", "health": "健康",
    "finance": "财务", "other": "其他",
}


def render() -> None:
    """渲染历史记录页面"""
    st.markdown("# 📜 分析历史")

    store = HistoryStore()
    _uid = st.session_state.get("logged_in_user", {}).get("id", "")

    # ── 决策分析历史 ──────────────────────────────────────────────
    st.markdown("### 分析报告")
    records = store.list_all(user_id=_uid)

    if not records:
        st.info("暂无分析记录，请先在「输入决策」页面提交分析。")
    else:
        st.markdown(f"共 **{len(records)}** 条记录")
        for i, record in enumerate(records):
            _render_record_card(i, record)

    # ── 模拟历史 ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 模拟记录")
    sim_records = store.list_simulations(user_id=_uid)

    if not sim_records:
        st.caption("暂无模拟记录，在分析报告中点击「运行心理模拟」即可生成。")
    else:
        st.markdown(f"共 **{len(sim_records)}** 条记录")
        for sim in sim_records:
            _render_sim_card(sim)

    # ── 底部操作 ─────────────────────────────────────────────────
    st.markdown("---")
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("清空所有记录", type="secondary", use_container_width=True):
            _clear_all_history(store)


def _render_sim_card(sim: dict) -> None:
    """渲染一条模拟记录卡片"""
    sim_id = sim["id"]
    title = sim.get("decision_title", "") or "未命名"
    created = sim["created_at"][:16].replace("T", " ") if sim.get("created_at") else ""
    timing = sim.get("timing_ms", 0)
    status = sim.get("status", "")

    with st.container(border=True):
        row = st.columns([4, 1, 1])
        with row[0]:
            st.markdown(f"**{title}**")
            parts = []
            if created:
                parts.append(f"{created}")
            if timing:
                parts.append(f"{timing / 1000:.1f}s")
            st.caption(" · ".join(parts) if parts else "")
        with row[1]:
            st.caption("已完成" if status == "completed" else "失败")
        with row[2]:
            if st.button("查看", key=f"view_sim_{sim_id}", use_container_width=True):
                _load_simulation(sim_id)


def _load_simulation(sim_id: str) -> None:
    """加载模拟结果到 session state 并跳转"""
    import json
    from src.models.simulation import EmotionalCurve

    store = HistoryStore()
    record = store.get_simulation(sim_id)
    if not record:
        st.error("模拟记录不存在或已损坏。")
        return

    try:
        # 新格式：curves_json 是数组
        curves_data = json.loads(record.get("curves_json", "[]") or "[]")
        if curves_data:
            curves = [EmotionalCurve(**c) for c in curves_data]
        else:
            # 旧格式兼容：curve_a_json + curve_b_json
            from src.models.simulation import EmotionalCurve as EC
            ca = record.get("curve_a_json", "{}")
            cb = record.get("curve_b_json", "{}")
            curves = []
            if ca and ca != "{}":
                curves.append(EC.model_validate_json(ca))
            if cb and cb != "{}":
                curves.append(EC.model_validate_json(cb))

        labels_data = json.loads(record.get("labels_json", "[]") or "[]")
        big_five_json = record.get("big_five_json", "{}")
        big_five = json.loads(big_five_json) if big_five_json != "{}" else None
    except Exception as e:
        st.error(f"加载模拟记录失败：{e}")
        return

    st.session_state.sim_result = {
        "curves": curves,
        "labels": labels_data,
        "big_five": big_five,
        "timing_ms": record.get("timing_ms", 0),
    }
    st.session_state.simulation_phase = "completed"
    st.session_state._sim_from_history = True  # 标记来自历史，不弹出完成横幅
    st.session_state.page = "simulation"
    st.rerun()


def _render_record_card(index: int, record: dict) -> None:
    """渲染一条历史记录卡片"""
    rid = record["id"]
    title = record["title"] or "未命名决策"
    created = record["created_at"][:16].replace("T", " ") if record.get("created_at") else ""
    category = record.get("category", "")
    user_context = record.get("user_context", "")
    insight = record.get("key_insight", "")
    bias_count = record.get("bias_count", 0)
    q_count = record.get("question_count", 0)
    style = record.get("decision_style", "")

    with st.container(border=True):
        row = st.columns([4, 1, 1, 1])

        with row[0]:
            st.markdown(f"**{title}**")
            cols = []
            if created:
                cols.append(f"{created}")
            if user_context:
                cols.append(f"{user_context}")
            if style:
                cols.append(f"{style}")
            st.caption(" · ".join(cols))

        with row[1]:
            st.caption(f"{bias_count} 个偏误")
        with row[2]:
            st.caption(f"{q_count} 个追问")

        with row[3]:
            if st.button("查看", key=f"view_{rid}", use_container_width=True):
                _load_history(rid)

        if insight:
            st.caption(insight)


def _load_history(report_id: str) -> None:
    """加载历史记录到当前会话并跳转到报告页"""
    store = HistoryStore()
    result = store.load_result(report_id)
    decision_input = store.load_decision_input(report_id)

    if result is None:
        st.error("无法加载该记录，数据可能已损坏。")
        return

    st.session_state.last_result = result
    st.session_state.last_decision_input = decision_input
    st.session_state.page = "report"
    st.rerun()


def _clear_all_history(store: HistoryStore) -> None:
    """清空所有历史记录（带二次确认）"""
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = True
        st.rerun()

    if st.session_state.get("confirm_clear"):
        st.warning("确定要清空所有历史记录吗？此操作不可恢复。")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("确认清空", type="primary", use_container_width=True):
                for r in store.list_all():
                    store.delete(r["id"])
                st.session_state.confirm_clear = False
                st.success("历史记录已清空。")
                st.rerun()
        with col2:
            if st.button("取消", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()
