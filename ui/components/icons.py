"""SVG 图标组件 — 生活预演家定制图标集

设计规范：
- 风格：Rounded + 双色调点缀
- 视口：24×24
- 主描边：2px，圆头端点，圆角连接
- 主色：#6366F1（Indigo）
- 辅色：#A5B4FC（浅 Indigo，透明度点缀）
- 每个图标包含主形状 + 微妙辅助元素
"""

from __future__ import annotations

_PRIMARY = "#6366F1"
_SECONDARY = "#A5B4FC"

_ICONS: dict[str, str] = {}

def _svg(d: str, secondary: str = "", view_box: str = "0 0 24 24") -> str:
    """构建完整 SVG 图标 HTML"""
    return f"""<svg width="22" height="22" viewBox="{view_box}" fill="none">
    <g stroke="{_PRIMARY}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        {d}
    </g>
    {secondary}
</svg>"""


# ── 编辑/输入 ──────────────────────────────
_ICONS["edit"] = _svg("""
    <path d="M14.5 3.5a2 2 0 0 1 2.8 2.8L7 17l-4 1 1-4 10.5-10.5Z"/>
    <path d="M12 6 6 12" opacity="0.3" stroke="#A5B4FC"/>
""")

# ── 图表/报告 ──────────────────────────────
_ICONS["chart"] = _svg("""
    <rect x="3" y="13" width="4" height="8" rx="1"/>
    <rect x="10" y="9" width="4" height="12" rx="1"/>
    <rect x="17" y="5" width="4" height="16" rx="1"/>
    <path d="M17 5 12 9 7 13" opacity="0.3" stroke="#A5B4FC" stroke-width="1.5"/>
""")

# ── 大脑/分析 ──────────────────────────────
_ICONS["brain"] = _svg("""
    <path d="M12 3a5.5 5.5 0 0 1 5.5 5.5c0 2-1 3.5-2.5 5"/>
    <path d="M12 3a5.5 5.5 0 0 0-5.5 5.5c0 2 1 3.5 2.5 5"/>
    <path d="M7 14c0 2 2 3.5 5 3.5s5-1.5 5-3.5"/>
    <path d="M10 14v4M14 14v4"/>
    <circle cx="12" cy="7" r="1.5" opacity="0.3" fill="#A5B4FC" stroke="none"/>
""")

# ── 对话框/追问 ────────────────────────────
_ICONS["thought"] = _svg("""
    <path d="M21 14a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v9Z"/>
    <circle cx="9" cy="10" r="1" opacity="0.3" fill="#A5B4FC" stroke="none"/>
    <circle cx="13" cy="10" r="1" opacity="0.3" fill="#A5B4FC" stroke="none"/>
    <circle cx="17" cy="10" r="1" opacity="0.3" fill="#A5B4FC" stroke="none"/>
""")

# ── 风格/创意 ──────────────────────────────
_ICONS["style"] = _svg("""
    <circle cx="12" cy="12" r="3"/>
    <path d="M12 1v3M12 20v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1 12h3M20 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>
    <circle cx="12" cy="12" r="8" opacity="0.15" stroke="#A5B4FC" stroke-width="1"/>
""")

# ── 历史/时钟 ──────────────────────────────
_ICONS["history"] = _svg("""
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
    <circle cx="12" cy="12" r="4" opacity="0.2" fill="#A5B4FC" stroke="none"/>
""")

# ── 播放/模拟 ──────────────────────────────
_ICONS["simulate"] = _svg("""
    <polygon points="6 3 20 12 6 21 6 3"/>
    <circle cx="6" cy="12" r="3" opacity="0.2" fill="#A5B4FC" stroke="none"/>
""")

# ── 用户/人格 ──────────────────────────────
_ICONS["personality"] = _svg("""
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
    <circle cx="12" cy="7" r="2" opacity="0.3" fill="#A5B4FC" stroke="none"/>
""")

# ── 开始/启动 ──────────────────────────────
_ICONS["start"] = _svg("""
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    <circle cx="12" cy="12" r="3" opacity="0.2" fill="#A5B4FC" stroke="none"/>
""")

# ── 删除 ────────────────────────────────────
_ICONS["trash"] = _svg("""
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    <line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>
""", secondary='<path d="M8 6h8" opacity="0.2" stroke="#A5B4FC" stroke-width="2" stroke-linecap="round"/>')

# ── 勾选/完成 ──────────────────────────────
_ICONS["check"] = _svg("""
    <polyline points="20 6 9 17 4 12"/>
    <circle cx="12" cy="12" r="3" opacity="0.15" fill="#A5B4FC" stroke="none"/>
""")

# ── 关闭 ────────────────────────────────────
_ICONS["close"] = _svg("""
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    <circle cx="12" cy="12" r="4" opacity="0.12" fill="#A5B4FC" stroke="none"/>
""")

# ── 文档/报告 ──────────────────────────────
_ICONS["report"] = _svg("""
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/>
    <path d="M14 2v6h6"/>
    <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
    <line x1="10" y1="9" x2="9" y2="9" opacity="0.3" stroke="#A5B4FC"/>
""")

# ── 问卷 ────────────────────────────────────
_ICONS["quiz"] = _svg("""
    <circle cx="12" cy="12" r="10"/>
    <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/>
    <line x1="12" y1="17" x2="12" y2="17"/>
    <circle cx="12" cy="12" r="5" opacity="0.15" fill="#A5B4FC" stroke="none"/>
""")

# ── 目标 ────────────────────────────────────
_ICONS["goal"] = _svg("""
    <circle cx="12" cy="12" r="10"/>
    <circle cx="12" cy="12" r="6"/>
    <circle cx="12" cy="12" r="2"/>
    <circle cx="12" cy="12" r="8" opacity="0.1" fill="#A5B4FC" stroke="none"/>
""")

# ── 箭头右 ──────────────────────────────────
_ICONS["arrow-right"] = _svg("""
    <line x1="5" y1="12" x2="19" y2="12"/>
    <polyline points="12 5 19 12 12 19"/>
""")

# ── 用户群 ──────────────────────────────────
_ICONS["users"] = _svg("""
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.9"/>
    <path d="M16 3.1a4 4 0 0 1 0 7.8"/>
    <circle cx="9" cy="7" r="2" opacity="0.3" fill="#A5B4FC" stroke="none"/>
""")

# ── 灯光/洞察 ──────────────────────────────
_ICONS["idea"] = _svg("""
    <path d="M9.5 14.5v-3a3 3 0 0 1 5 0v3"/>
    <path d="M9.5 17.5h5"/>
    <path d="M10 20.5h4"/>
    <path d="M12 2.5v1"/>
    <path d="M4.2 5.7l1.1 1.1" opacity="0.4" stroke="#A5B4FC"/>
    <path d="M19.8 5.7l-1.1 1.1" opacity="0.4" stroke="#A5B4FC"/>
    <circle cx="12" cy="11" r="1" opacity="0.3" fill="#A5B4FC" stroke="none"/>
""")

# ── 天平/决策 ──────────────────────────────
_ICONS["balance"] = _svg("""
    <line x1="4" y1="7" x2="20" y2="7"/>
    <polyline points="4 7 6 20 10 20"/>
    <polyline points="20 7 18 20 14 20"/>
    <circle cx="12" cy="7" r="2" opacity="0.2" fill="#A5B4FC" stroke="none"/>
""")

# ── 函数调用 ────────────────────────────────

def icon(name: str, size: int = 22, color: str = "") -> str:
    """返回内联 SVG 图标 HTML"""
    svg = _ICONS.get(name, "")
    if not svg:
        return f"<!-- icon '{name}' not found -->"
    svg = svg.replace('width="22"', f'width="{size}"').replace('height="22"', f'height="{size}"')
    if color:
        svg = svg.replace(_PRIMARY, color).replace(_SECONDARY, color + "80")
    return svg


def icon_text(name: str, text: str, size: int = 22, gap: int = 8, color: str = "") -> str:
    """图标 + 文字组合"""
    svg = icon(name, size=size, color=color)
    return (
        f'<span style="display:inline-flex;align-items:center;gap:{gap}px;">'
        f'{svg}<span>{text}</span></span>'
    )
