"""全局样式 — 遵循品牌指南的设计系统

品牌：生活预演家
主色：#6366F1 Indigo
基调：沉静、可信、温暖、理性
字体：Inter + 系统中文堆栈
"""

import streamlit as st


def inject_global_css() -> None:
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {{
        --primary: #6366F1;
        --primary-hover: #4F46E5;
        --primary-light: #E0E7FF;
        --primary-bg: #F5F3FF;
        --success: #059669;
        --warning: #D97706;
        --danger: #DC2626;
        --info: #2563EB;
        --text: #0F172A;
        --text-secondary: #475569;
        --text-muted: #94A3B8;
        --border: #E0E7FF;
        --card: #FFFFFF;
        --bg: #F5F3FF;
        --shadow-sm: 0 1px 2px rgba(99,102,241,0.04);
        --shadow-md: 0 4px 12px rgba(99,102,241,0.06), 0 1px 3px rgba(99,102,241,0.04);
        --shadow-lg: 0 8px 24px rgba(99,102,241,0.08), 0 2px 6px rgba(99,102,241,0.04);
        --radius: 10px;
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }}
    .stApp {{ background: var(--bg); }}

    /* ── 侧边栏 ────────────────────────────────── */
    section[data-testid="stSidebar"] > div:first-child {{
        background: linear-gradient(180deg, #0F172A 0%, #1a2744 100%) !important;
    }}
    section[data-testid="stSidebar"] > div:first-child::before {{
        content: '' !important; display: block !important;
        height: 2px !important; width: 28px !important;
        background: var(--primary) !important; border-radius: 1px !important;
        margin: 1.5rem 1rem 0.5rem !important;
    }}
    section[data-testid="stSidebar"] * {{ color: #94A3B8 !important; }}
    section[data-testid="stSidebar"] strong {{ color: #F1F5F9 !important; font-weight: 600; }}
    section[data-testid="stSidebar"] .stCaption {{ color: #64748B !important; }}

    /* ── 标题 ──────────────────────────────────── */
    h1 {{ font-weight: 700; font-size: 1.6rem; letter-spacing: -0.02em; color: var(--text); }}
    h2 {{ font-weight: 600; font-size: 1.2rem; letter-spacing: -0.01em; color: var(--text); padding-bottom: 0.35rem; border-bottom: 1px solid var(--border); margin-top: 0.5rem; }}
    h3 {{ font-weight: 600; font-size: 1rem; color: var(--text); }}

    /* ── 导航按钮 ──────────────────────────────── */
    div.row-widget.stButton button {{
        border-radius: 6px; font-weight: 500; font-size: 0.8rem;
        padding: 0.3rem 0.5rem; border: 1px solid var(--border);
        background: var(--card); color: var(--text-secondary);
        transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
    }}
    div.row-widget.stButton button[kind="primary"] {{
        background: var(--primary); color: white; border-color: var(--primary);
    }}
    div.row-widget.stButton button[kind="primary"]:hover {{
        background: var(--primary-hover); box-shadow: 0 4px 12px rgba(99,102,241,0.3);
        transform: translateY(-1px);
    }}

    /* ── 按钮 ──────────────────────────────────── */
    .stButton button {{
        border-radius: 8px; font-weight: 500; font-size: 0.85rem;
        padding: 0.4rem 1.2rem; border: 1px solid var(--border);
        background: var(--card); color: var(--text);
        transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
    }}
    .stButton button[kind="primary"] {{
        background: var(--primary); color: white; border-color: var(--primary);
    }}
    .stButton button[kind="primary"]:hover {{
        background: var(--primary-hover);
        box-shadow: 0 4px 14px rgba(99,102,241,0.35);
        transform: translateY(-1px);
    }}

    /* ── 卡片 ──────────────────────────────────── */
    div[data-testid="stContainer"] {{
        background: var(--card); border-radius: var(--radius);
        padding: 1.2rem; box-shadow: var(--shadow-sm);
        border: 1px solid var(--border); margin-bottom: 0.75rem;
    }}
    div[data-testid="stContainer"]:hover {{
        box-shadow: var(--shadow-md);
    }}

    /* ── 指标卡 ────────────────────────────────── */
    div[data-testid="stMetric"] {{
        background: var(--card); border-radius: 10px;
        padding: 0.75rem 1rem; border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }}
    div[data-testid="stMetric"] label {{
        color: var(--text-muted); font-size: 0.7rem;
        font-weight: 500; letter-spacing: 0.03em;
        text-transform: uppercase;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        font-size: 1.4rem; font-weight: 700; color: var(--text);
        letter-spacing: -0.02em;
    }}

    /* ── 提示框 ────────────────────────────────── */
    div.stSuccess {{ background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; border-radius: 10px; padding: 0.75rem 1rem; font-size: 0.85rem; }}
    div.stInfo {{ background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; border-radius: 10px; padding: 0.75rem 1rem; font-size: 0.85rem; }}
    div.stWarning {{ background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; border-radius: 10px; padding: 0.75rem 1rem; font-size: 0.85rem; }}
    div.stError {{ background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; border-radius: 10px; padding: 0.75rem 1rem; font-size: 0.85rem; }}

    /* ── 进度条 ────────────────────────────────── */
    div.stProgress > div > div > div > div {{
        background: linear-gradient(90deg, var(--primary), #818CF8); border-radius: 10px;
    }}
    div.stProgress > div > div {{ background: var(--border); border-radius: 10px; height: 5px; }}

    /* ── 分割线 ────────────────────────────────── */
    hr {{ margin: 1rem 0; border: none; border-top: 1px solid var(--border); }}

    /* ── 说明文字 ──────────────────────────────── */
    .stCaption {{ color: var(--text-muted); font-size: 0.78rem; }}

    /* ── 选项卡 ────────────────────────────────── */
    button[data-baseweb="tab"] {{ font-size: 0.85rem; font-weight: 500; color: var(--text-secondary); padding: 0.4rem 0.8rem; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: var(--primary); font-weight: 600; }}

    /* ── 展开面板 ──────────────────────────────── */
    details {{ border-radius: 10px; border: 1px solid var(--border); background: var(--card); padding: 0.5rem 0.8rem; margin-bottom: 0.5rem; box-shadow: var(--shadow-sm); }}

    /* ── 文本输入框 ────────────────────────────── */
    textarea, input[type="text"], input[type="number"] {{
        border-radius: 8px !important; border: 1px solid var(--border) !important;
        font-family: 'Inter', sans-serif !important; font-size: 0.9rem !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    textarea:focus, input[type="text"]:focus {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    }}

    /* ── 下拉框 ────────────────────────────────── */
    div[data-baseweb="select"] > div {{ border-radius: 8px !important; border-color: var(--border) !important; font-size: 0.85rem; }}

    /* ── 滑块 ──────────────────────────────────── */
    div[data-testid="stSlider"] div[data-testid="stThumb"] {{ background: var(--primary) !important; }}
    div[data-testid="stSlider"] div[role="slider"] {{ background: var(--primary) !important; }}

    /* ── 数据表格 ──────────────────────────────── */
    div[data-testid="stDataFrame"] {{ border-radius: 8px; border: 1px solid var(--border); }}
    </style>
    """, unsafe_allow_html=True)
