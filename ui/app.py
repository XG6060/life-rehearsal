"""Streamlit 主入口

启动方式：
    streamlit run ui/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from config.settings import settings
from src.db.history_store import HistoryStore
from ui.components.style import inject_global_css
from ui.pages._01_decision_input import reset_form_data, sync_thread_result
from ui.pages._04_simulation import check_sim_result, reset_all_sim_state

st.set_page_config(
    page_title="生活预演家",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 注入全局 CSS ───────────────────────────────────────────────────
inject_global_css()

# ── 登录检查 ─────────────────────────────────────────────────────
if "logged_in_user" not in st.session_state:
    from ui.pages._00_login import render as render_login
    render_login()
    st.stop()

# ── 同步后台线程结果 → session state（每次脚本执行都会运行）───────
# 后台线程用模块级全局变量通信（st.session_state 在后台线程不可用）
sync_thread_result()


# ── Fragment：分析期间静默检测完成状态 ────────────────────────────
# 不渲染任何可见内容，只是每 3 秒检查一次后台分析是否完成。
# 完成时调用 st.rerun() 触发全页面刷新以显示完成横幅。
# 用 @st.fragment 而非 time.sleep + st.rerun()，因为后者会阻塞
# 主线程导致元素叠加和混乱。
@st.fragment(run_every=3.0)
def _check_completions():
    """静默检测后台分析/模拟状态，完成后触发全页面刷新。"""
    sim_ready = check_sim_result()
    sync_thread_result()

    if st.session_state.get("analysis_complete", False):
        st.rerun()
    elif sim_ready:
        # 模拟刚完成，刷新页面显示横幅
        st.rerun()
    elif st.session_state.get("analysis_running", False):
        st.empty()
    elif st.session_state.get("simulation_phase") == "running":
        st.empty()

# ── 初始化 session_state ─────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state.page = "input"
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "simulation_phase" not in st.session_state:
    st.session_state.simulation_phase = "quiz"

# ── 侧边栏 ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 生活预演家")
    st.caption(f"v{settings.app_version}  ·  AI 决策模拟")

    st.markdown("---")
    st.markdown("**使用流程**")
    st.markdown(
        "1. 描述你的决策困境\n"
        "2. 获取 AI 分析报告\n"
        "3. 运行心理模拟\n"
        "4. 对比各选项结果"
    )

    st.markdown("---")
    st.markdown("**隐私说明**")
    st.markdown("数据本地存储，使用 DeepSeek API 进行分析。")

    if not settings.has_api_key:
        st.warning("未配置 API Key", icon=None)
    else:
        st.caption("API 已就绪")

    # 当前用户
    user = st.session_state.get("logged_in_user")
    if user:
        st.markdown("---")
        st.caption(f"用户: {user.get('nickname') or user.get('email')}")
        if st.button("退出登录", use_container_width=True):
            st.session_state.pop("logged_in_user", None)
            st.rerun()

        # 修改密码
        with st.expander("修改密码"):
            with st.form("change_pwd_form"):
                old_pwd = st.text_input("原密码", type="password", placeholder="输入原密码")
                new_pwd = st.text_input("新密码", type="password", placeholder="至少 6 位")
                cfm_pwd = st.text_input("确认新密码", type="password", placeholder="再次输入")
                if st.form_submit_button("确认修改", use_container_width=True):
                    if not old_pwd or not new_pwd:
                        st.error("请填写所有字段")
                    elif new_pwd != cfm_pwd:
                        st.error("两次新密码不一致")
                    else:
                        from src.services.auth_service import AuthService
                        auth = AuthService()
                        result = auth.change_password(user["id"], old_pwd, new_pwd)
                        if result["ok"]:
                            st.success("密码修改成功")
                        else:
                            st.error(result["error"])

    # 后台分析状态
    if st.session_state.get("analysis_running"):
        st.info("后台分析中...")

# ── 分析完成通知横幅 ──────────────────────────────────────────────

_complete = st.session_state.get("analysis_complete", False)
if _complete:
    _pending = st.session_state.get("pending_result", None)
    if _pending is not None:
        ac_cols = st.columns([6, 1, 1])
        with ac_cols[0]:
            st.success("✅ **分析已完成！** 是否将当前报告替换为新分析结果？", icon="✅")
        with ac_cols[1]:
            if st.button("替换", use_container_width=True, type="primary"):
                _store = HistoryStore()
                _uid = st.session_state.get("logged_in_user", {}).get("id", "")
                _store.save(st.session_state.pending_result, st.session_state.pending_input, user_id=_uid)
                st.session_state.last_result = st.session_state.pending_result
                st.session_state.last_decision_input = st.session_state.pending_input
                st.session_state.analysis_complete = False
                st.session_state.analysis_running = False
                st.session_state.pending_result = None
                reset_form_data()
                st.session_state.page = "report"
                st.rerun()
        with ac_cols[2]:
            if st.button("不替换", use_container_width=True):
                st.session_state.analysis_complete = False
                st.session_state.pending_result = None
                st.rerun()

# ── 分析出错通知 ─────────────────────────────────────────────────

_error = st.session_state.get("analysis_error", None)
if _error:
    st.error(f"分析出错：{_error}")

# ── 模拟完成通知横幅 ─────────────────────────────────────────────

# 模拟完成横幅（只在新完成时显示，查看历史时不显示）
if (st.session_state.get("simulation_phase") == "completed"
    and st.session_state.get("sim_result") is not None
    and not st.session_state.get("_sim_from_history", False)):
    _sim_result = st.session_state.sim_result
    _n_curves = len(_sim_result.get("curves", []))
    _timing = _sim_result.get("timing_ms", 0)
    btn_cols = st.columns([6, 1, 1])
    with btn_cols[0]:
        st.success(
            f"✅ **模拟已完成！** {_n_curves} 个选项已模拟完成（{_timing / 1000:.1f}s）",
            icon="✅",
        )
    with btn_cols[1]:
        if st.button("查看结果", use_container_width=True, type="primary"):
            st.session_state.page = "simulation"
            st.rerun()
    with btn_cols[2]:
        if st.button("关闭", use_container_width=True):
            reset_all_sim_state()
            st.rerun()

# ── 导航按钮 ─────────────────────────────────────────────────────

_nav_labels = {
    "input": ("输入"),
    "report": ("报告"),
    "simulation": ("模拟"),
    "history": ("历史"),
}
_nav_cols = st.columns(len(_nav_labels))
for i, (page_key, label) in enumerate(_nav_labels.items()):
    with _nav_cols[i]:
        if st.button(label, use_container_width=True,
                     type="primary" if st.session_state.page == page_key else "secondary"):
            st.session_state.page = page_key
            st.rerun()

st.markdown("---")

# ── 页面路由 ─────────────────────────────────────────────────────

if st.session_state.page == "input":
    from ui.pages._01_decision_input import render
    render()
elif st.session_state.page == "report":
    from ui.pages._02_analysis_report import render
    render()
elif st.session_state.page == "history":
    from ui.pages._03_history import render
    render()
elif st.session_state.page == "simulation":
    from ui.pages._04_simulation import render
    render()


# ── 启动后台监控（分析或模拟运行时激活）─────────────────────────
if st.session_state.get("analysis_running", False) or st.session_state.get("simulation_phase") == "running":
    _check_completions()
