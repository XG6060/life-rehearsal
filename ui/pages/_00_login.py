"""登录页面 — 左右分屏（左品牌 + 右表单，统一深色背景）"""

from __future__ import annotations

import streamlit as st

from src.services.auth_service import AuthService
import streamlit.components.v1 as components


def render() -> None:
    _inject_style()

    left, right = st.columns([5, 4])

    with left:
        _render_brand()

    with right:
        for _ in range(12):
            st.markdown("")
        tab_login, tab_register, tab_forgot = st.tabs(["登录", "注册", "找回密码"])
        with tab_login:
            with st.form("login_form"):
                login_email = st.text_input("邮箱", placeholder="your@email.com")
                login_pwd = st.text_input("密码", type="password", placeholder="输入密码")
                if st.form_submit_button("登录", use_container_width=True, type="primary"):
                    if not login_email or not login_pwd:
                        st.error("请填写邮箱和密码")
                    else:
                        auth = AuthService()
                        result = auth.login(login_email, login_pwd)
                        if result["ok"]:
                            st.session_state.logged_in_user = result["user"]
                            st.rerun()
                        else:
                            st.error(result["error"])
        with tab_register:
            with st.form("register_form"):
                reg_email = st.text_input("邮箱", placeholder="your@email.com")
                reg_nick = st.text_input("昵称（选填）", placeholder="如何称呼你")
                reg_pwd = st.text_input("密码", type="password", placeholder="至少 6 位")
                reg_cfm = st.text_input("确认密码", type="password", placeholder="再次输入密码")
                reg_sq = st.selectbox("密保问题（找回密码用）",
                    ["你小学班主任叫什么？", "你最好的朋友叫什么？",
                     "你的出生地在哪？", "你最喜欢的书是什么？",
                     "自定义密保问题"])
                if reg_sq == "自定义密保问题":
                    reg_sq = st.text_input("请输入你的密保问题")
                reg_sa = st.text_input("密保答案", placeholder="输入答案")
                if st.form_submit_button("注册", use_container_width=True, type="primary"):
                    if not reg_email or not reg_pwd:
                        st.error("请填写邮箱和密码")
                    elif reg_pwd != reg_cfm:
                        st.error("两次密码不一致")
                    elif not reg_sq or not reg_sa:
                        st.error("请设置密保问题和答案")
                    else:
                        auth = AuthService()
                        result = auth.register(reg_email, reg_pwd, reg_nick, reg_sq, reg_sa)
                        if result["ok"]:
                            st.session_state.logged_in_user = result["user"]
                            st.rerun()
                        else:
                            st.error(result["error"])
        with tab_forgot:
            if "forgot_step" not in st.session_state:
                st.session_state.forgot_step = 1
            if "forgot_email_sq" not in st.session_state:
                st.session_state.forgot_email_sq = ""
            if "forgot_question" not in st.session_state:
                st.session_state.forgot_question = ""

            if st.session_state.forgot_step == 1:
                with st.form("forgot_step1"):
                    forgot_email = st.text_input("注册邮箱", placeholder="your@email.com")
                    if st.form_submit_button("查询密保问题", use_container_width=True, type="primary"):
                        auth = AuthService()
                        q = auth.get_security_question(forgot_email)
                        if not q:
                            st.error("该邮箱未注册或未设置密保问题")
                        else:
                            st.session_state.forgot_email_sq = forgot_email
                            st.session_state.forgot_question = q
                            st.session_state.forgot_step = 2
                            st.rerun()
            elif st.session_state.forgot_step == 2:
                st.info(f"密保问题：{st.session_state.forgot_question}")
                with st.form("forgot_step2"):
                    answer = st.text_input("密保答案", placeholder="输入答案")
                    if st.form_submit_button("验证答案", use_container_width=True, type="primary"):
                        auth = AuthService()
                        r = auth.verify_security_answer(st.session_state.forgot_email_sq, answer)
                        if r["ok"]:
                            st.session_state.forgot_step = 3
                            st.rerun()
                        else:
                            st.error(r["error"])
            elif st.session_state.forgot_step == 3:
                st.success("密保验证通过！")
                with st.form("forgot_step3"):
                    new_pwd = st.text_input("新密码", type="password", placeholder="至少 6 位")
                    new_cfm = st.text_input("确认新密码", type="password", placeholder="再次输入")
                    if st.form_submit_button("重置密码", use_container_width=True, type="primary"):
                        if not new_pwd:
                            st.error("请输入新密码")
                        elif new_pwd != new_cfm:
                            st.error("两次密码不一致")
                        else:
                            auth = AuthService()
                            result = auth.reset_password(st.session_state.forgot_email_sq, new_pwd)
                            if result["ok"]:
                                st.success("密码已重置，请登录")
                                st.session_state.forgot_step = 1
                                st.rerun()
                            else:
                                st.error(result["error"])


def _inject_style():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] {display: none !important;}
    html, body, #root, [data-testid="stAppViewContainer"], .main {overflow: hidden !important; height: 100vh !important; max-height: 100vh !important;}
    .stApp > header {display: none !important;}
    .main > div:first-child {padding: 0 !important;}
    .block-container {padding: 0 !important; max-width: none !important;}

    .stApp {background: #0F172A !important; overflow: hidden !important; max-height: 100vh !important;}

    .brand-panel {
        min-height: 100vh; width: 100%; position: relative; overflow: hidden;
    }
    .particle {
        position: absolute; border-radius: 50%;
        background: rgba(99,102,241,0.12);
        animation: float linear infinite;
    }
    @keyframes float {
        0% {transform: translateY(100vh) scale(0); opacity: 0;}
        10% {opacity: 1;}
        90% {opacity: 0.2;}
        100% {transform: translateY(-10vh) scale(1); opacity: 0;}
    }
    .p1 {width:6px;height:6px;left:10%;animation-duration:18s;animation-delay:0s;}
    .p2 {width:10px;height:10px;left:25%;animation-duration:22s;animation-delay:2s;}
    .p3 {width:4px;height:4px;left:40%;animation-duration:15s;animation-delay:4s;}
    .p4 {width:8px;height:8px;left:55%;animation-duration:20s;animation-delay:1s;}
    .p5 {width:5px;height:5px;left:70%;animation-duration:25s;animation-delay:3s;}
    .p6 {width:12px;height:12px;left:85%;animation-duration:17s;animation-delay:5s;}
    .p7 {width:7px;height:7px;left:50%;animation-duration:28s;animation-delay:0s;}

    .brand-title {font-size:2.5rem;font-weight:700;color:#F1F5F9;letter-spacing:-0.02em;position:relative;z-index:1;}
    .brand-sub {font-size:0.95rem;color:#94A3B8;margin:0.5rem 0 2rem;position:relative;z-index:1;}
    .feature {display:flex;align-items:center;gap:10px;margin-bottom:0.9rem;color:#CBD5E1;font-size:0.88rem;position:relative;z-index:1;}
    .feature::before {content:'';width:6px;height:6px;border-radius:50%;background:#6366F1;flex-shrink:0;}
    .brand-footer {color:#475569;font-size:0.78rem;margin-top:2.5rem;position:relative;z-index:1;}
    .accent {width:40px;height:3px;background:#6366F1;border-radius:2px;margin-bottom:1rem;position:relative;z-index:1;}

    .stTabs button {color:#94A3B8 !important;}
    .stTabs button[aria-selected="true"] {color:#E2E8F0 !important;}
    .stTextInput label {color:#CBD5E1 !important;}
    .stTextInput input {
    background:#1a2744 !important;
    border:1px solid rgba(99,102,241,0.3) !important;
    color:#F1F5F9 !important;
    border-radius:8px !important;
    font-size:0.9rem !important;
    padding:8px 12px !important;
    caret-color:#6366F1 !important;
}
.stTextInput input:focus {
    border-color:#6366F1 !important;
    box-shadow:0 0 0 3px rgba(99,102,241,0.2) !important;
}
.stTextInput input::placeholder {color:#94A3B8 !important;opacity:1 !important;}
.stTextInput input:-webkit-autofill,
.stTextInput input:-webkit-autofill:hover,
.stTextInput input:-webkit-autofill:focus {
    -webkit-text-fill-color:#F1F5F9 !important;
    -webkit-box-shadow:0 0 0 30px #1a2744 inset !important;
    caret-color:#6366F1 !important;
}
    .stForm {padding:0 !important;}
    .stTextInput input:-webkit-autofill,
    .stTextInput input:-webkit-autofill:hover,
    .stTextInput input:-webkit-autofill:focus {
        -webkit-text-fill-color: #FFFFFF !important;
        -webkit-box-shadow: 0 0 0 30px rgba(30,40,70,1) inset !important;
        transition: background-color 5000s ease-in-out 0s;
    }
    .stError {background:rgba(239,68,68,0.1) !important;border:1px solid rgba(239,68,68,0.2) !important;color:#FCA5A5 !important;}
    </style>
    """, unsafe_allow_html=True)


def _render_brand():
    import os
    _scene_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'components', 'scene.html')
    if not os.path.exists(_scene_path):
        _scene_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'scene.html')
    with open(_scene_path, 'r', encoding='utf-8') as _f:
        html = _f.read()
    components.html(html, height=1000)


