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
        tab_login, tab_register = st.tabs(["登录", "注册"])
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
                col_code, col_btn = st.columns([3, 2])
                with col_code:
                    reg_code = st.text_input("验证码", placeholder="6 位数字")
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    send_clicked = st.form_submit_button("发送验证码", use_container_width=True)
                if reg_email and send_clicked:
                    from src.services.email_service import generate_code, send_verification_email
                    code = generate_code(reg_email)
                    if send_verification_email(reg_email, code):
                        st.success(f"验证码已发送至 {reg_email}")
                    else:
                        st.error("发送失败，请检查邮箱地址")
                if st.form_submit_button("注册", use_container_width=True, type="primary"):
                    if not reg_email or not reg_pwd:
                        st.error("请填写邮箱和密码")
                    elif reg_pwd != reg_cfm:
                        st.error("两次密码不一致")
                    elif not reg_code:
                        st.error("请输入验证码")
                    else:
                        from src.services.email_service import verify_code
                        if not verify_code(reg_email, reg_code):
                            st.error("验证码错误或已过期")
                        else:
                            auth = AuthService()
                            result = auth.register(reg_email, reg_pwd, reg_nick)
                            if result["ok"]:
                                st.session_state.logged_in_user = result["user"]
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


