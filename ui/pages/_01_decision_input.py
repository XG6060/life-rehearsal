"""决策信息输入页面 — 后台分析，用户可自由切换页面"""

from __future__ import annotations

import re
import threading

import streamlit as st

from config.settings import settings
from src.models.decision import DecisionCreate
from src.services.decision_service import DecisionService

# ── 线程间通信：后台线程 → 主线程 ──────────────────────────────────
# st.session_state 不能在后台线程中访问（无 ScriptRunContext），
# 所以用模块级变量做线程间通信，主线程在每次脚本执行时同步到 session state。
_THREAD_RESULT: dict = {}
_THREAD_LOCK = threading.Lock()

_FORM_DEFAULTS = {
    "title": "",
    "category": "职业",
    "age_range": "",
    "occupation": "",
    "city": "",
    "context": "",
    "option_a": "",
    "option_a_desc": "",
    "option_b": "",
    "option_b_desc": "",
}

# 下拉选项常量（用于合理性提示和表单重置）
_AGE_OPTIONS = ["", "18岁以下", "18-24", "25-30", "31-35", "36-40", "40以上"]
_OCC_OPTIONS = ["", "互联网/IT", "金融/咨询", "教育/科研", "医疗/健康",
                "制造业/工程", "房地产/建筑", "传媒/广告", "政府/事业单位",
                "销售/市场", "自由职业", "学生", "其他"]
_CITY_OPTIONS = ["", "一线城市（北上广深）", "新一线城市（成都/杭州等）",
                 "二线城市", "三线及以下城市", "县城/乡镇"]


def _init_form_data():
    if "form_data" not in st.session_state:
        st.session_state.form_data = dict(_FORM_DEFAULTS)
    if "analysis_running" not in st.session_state:
        st.session_state.analysis_running = False
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "analysis_error" not in st.session_state:
        st.session_state.analysis_error = None


def sync_thread_result():
    """主线程调用：将后台线程的分析结果同步到 st.session_state。"""
    global _THREAD_RESULT
    with _THREAD_LOCK:
        if not _THREAD_RESULT.get("ready"):
            return
        if _THREAD_RESULT.get("error"):
            st.session_state.analysis_error = _THREAD_RESULT["error"]
        else:
            st.session_state.pending_result = _THREAD_RESULT.get("result")
            st.session_state.pending_input = _THREAD_RESULT.get("input")
            st.session_state.analysis_complete = True
        st.session_state.analysis_running = False
        _THREAD_RESULT = {}  # 清空，避免重复消费


def reset_form_data():
    """清空输入页面的表单数据，用于替换报告后重置。"""
    st.session_state.form_data = dict(_FORM_DEFAULTS)


def render() -> None:
    _init_form_data()
    fd = st.session_state.form_data

    # ── 如果分析在运行中，显示状态提示 ──────────────────────────────
    if st.session_state.get("analysis_running"):
        st.info("⏳ AI 正在后台分析中，你可以切换到其他页面浏览，分析完成后页面顶部会有通知。")
        return

    st.markdown("# 📝 描述你的决策困境")
    st.markdown("花几分钟描述你正在纠结的决定。写得越详细，分析越准确。")
    st.markdown("---")

    # ── 场景快速选择 ──────────────────────────────────────────────
    st.markdown("### 快速选择场景（可选）")
    scenario_options = {
        "自定义": "",
        "裸辞/换工作": "career",
        "分手": "relationship",
        "搬家/换城市": "relocation",
        "考研/留学": "education",
        "生孩子": "family",
    }
    st.selectbox(
        "选择一个常见场景作为起点（可修改）",
        options=list(scenario_options.keys()),
        index=0,
        key="scenario_selector",
    )

    # ── 输入区域 ──────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        fd["title"] = st.text_input(
            "**你的决策问题** 🎯",
            value=fd["title"],
            placeholder="例如：25岁，工作两年，要不要裸辞考研",
            help="用一句话概括你在纠结什么",
            key="input_title",
        )
    with col2:
        fd["category"] = st.selectbox(
            "**类别**",
            options=["职业", "感情", "搬家", "求学", "家庭", "其他"],
            index=["职业", "感情", "搬家", "求学", "家庭", "其他"].index(fd["category"])
            if fd["category"] in ["职业", "感情", "搬家", "求学", "家庭", "其他"]
            else 0,
            key="input_category",
        )

    st.markdown("### 关于你（匿名，有助于分析）")
    st.caption("如实填写能让 AI 分析更贴合你的实际情况，结果也会更准确。")
    col1, col2, col3 = st.columns(3)
    with col1:
        fd["age_range"] = st.selectbox(
            "年龄段",
            options=_AGE_OPTIONS,
            index=_AGE_OPTIONS.index(fd["age_range"]) if fd["age_range"] in _AGE_OPTIONS else 0,
            key="input_age",
        )
    with col2:
        fd["occupation"] = st.selectbox(
            "职业类别（选填）",
            options=_OCC_OPTIONS,
            index=_OCC_OPTIONS.index(fd["occupation"]) if fd["occupation"] in _OCC_OPTIONS else 0,
            key="input_occupation",
        )
    with col3:
        fd["city"] = st.selectbox(
            "城市类型（选填）",
            options=_CITY_OPTIONS,
            index=_CITY_OPTIONS.index(fd["city"]) if fd["city"] in _CITY_OPTIONS else 0,
            key="input_city",
        )

    st.markdown("### 详细描述你的困境 ✍️")
    st.markdown(
        "建议包含以下内容：\n"
        "- **现状**：现在的情况是什么样的\n"
        "- **纠结**：你在哪几个选项之间犹豫\n"
        "- **担心**：你最担心什么\n"
        "- **期望**：你希望通过这个决定得到什么",
    )
    fd["context"] = st.text_area(
        "把你的想法写下来",
        value=fd["context"],
        placeholder=(
            "比如：我今年26岁，在一家互联网公司做运营，工作了两年。"
            "工作内容越来越重复，感觉学不到东西了。"
            "我想裸辞考研，但又担心考不上...\n\n"
            "A 方案：辞职全身心备考\n"
            "B 方案：在职备考，边工作边复习\n"
            "C 方案：不考研了，换个工作"
        ),
        height=250,
        help="写得越具体，分析越有针对性",
        key="input_context",
    )

    with st.expander("补充选项信息（选填）"):
        st.markdown("如果你想手动补充选项细节：")
        fd["option_a"] = st.text_input("选项 A 名称", value=fd["option_a"], placeholder="如：辞职考研", key="input_opt_a")
        fd["option_a_desc"] = st.text_area("选项 A 描述", value=fd["option_a_desc"], placeholder="这个选项具体是什么？", height=80, key="input_opt_a_desc")
        fd["option_b"] = st.text_input("选项 B 名称", value=fd["option_b"], placeholder="如：在职备考", key="input_opt_b")
        fd["option_b_desc"] = st.text_area("选项 B 描述", value=fd["option_b_desc"], placeholder="这个选项具体是什么？", height=80, key="input_opt_b_desc")

    # ── 提交按钮 ────────────────────────────────────────────────────
    submitted = st.button(
        "开始分析",
        use_container_width=True,
        type="primary",
        disabled=not settings.has_api_key,
    )

    # ── 处理提交（后台线程分析） ─────────────────────────────────────
    if submitted:
        title = fd["title"]
        context = fd["context"]

        if not title or not context:
            st.error("请至少填写决策问题和详细描述。")
            return

        if len(context) < 30:
            st.warning("描述建议写得更详细一些（至少30字），分析结果会更准确。")

        # ── 输入质量检测 ───────────────────────────────────────────
        quality_warnings = []

        # 检测重复：连续重复 3 次以上的短语
        repeats = re.findall(r'([一-鿿]{2,})(?=\1{2,})', context)
        if repeats:
            quality_warnings.append("描述中存在大量重复内容，建议补充更多具体信息，分析会更准确。")

        # 检测情绪空洞：全是情绪词但没有事实描述
        emotion_words = ["烦", "焦虑", "纠结", "难受", "痛苦", "崩溃", "烦死了", "怎么办", "好烦"]
        emotion_count = sum(context.count(w) for w in emotion_words)
        has_facts = any(w in context for w in ["工作", "公司", "钱", "收入", "年龄", "时间",
                                                "家人", "朋友", "现在", "目前", "已经"])
        if emotion_count > 5 and not has_facts:
            quality_warnings.append("描述中情绪化的内容较多，建议补充一些具体事实（工作情况、收入、年龄、家庭情况等），分析会更有针对性。")

        # 检测字符单一：超过 60% 都是同一个字符
        if len(context) > 20:
            most_common = max(set(context), key=context.count)
            if context.count(most_common) / len(context) > 0.6:
                quality_warnings.append("描述的内容过于重复，建议用更具体的语言描述你的实际情况。")

        for warning in quality_warnings:
            st.warning(f"⚠️ {warning}")

        # ── 用户信息合理性提示 ─────────────────────────────────────
        if fd["age_range"]:
            age_keywords = {"18岁以下": ["18", "未成年", "高中"], "18-24": ["20", "大学", "毕业"],
                            "25-30": ["25", "26", "27", "28", "29", "毕业几年", "工作几年"],
                            "31-35": ["30", "31", "32", "33", "34", "35", "中年"],
                            "36-40": ["35", "36", "37", "38", "39", "40", "中年"],
                            "40以上": ["40", "45", "50", "中年", "退休"]}
            matching_keywords = [k for k in age_keywords.get(fd["age_range"], []) if k in context]
            if not matching_keywords and len(context) > 50:
                st.caption(f"💡 你选的年龄段是「{fd['age_range']}」，如果描述中提到的年龄与选择不符可以修改，这样分析会更准确。")

        category_map = {
            "职业": "career", "感情": "relationship", "搬家": "relocation",
            "求学": "education", "家庭": "family", "其他": "other",
        }

        options = []
        if fd["option_a"]:
            options.append({"label": f"A：{fd['option_a']}", "description": fd["option_a_desc"] or ""})
        if fd["option_b"]:
            options.append({"label": f"B：{fd['option_b']}", "description": fd["option_b_desc"] or ""})

        input_data = DecisionCreate(
            title=title,
            category=category_map.get(fd["category"], "other"),
            context=context,
            options=options,
            age_range=fd["age_range"],
            occupation_category=fd["occupation"],
            city_tier=fd["city"],
        )

        # 在后台线程中运行分析（用模块级变量通信，不用 st.session_state）
        def _run_analysis():
            global _THREAD_RESULT
            try:
                service = DecisionService()
                result = service.analyze_from_input(input_data)
                with _THREAD_LOCK:
                    _THREAD_RESULT = {
                        "ready": True,
                        "result": result,
                        "input": input_data,
                        "error": None,
                    }
            except Exception as e:
                with _THREAD_LOCK:
                    _THREAD_RESULT = {
                        "ready": True,
                        "result": None,
                        "input": None,
                        "error": str(e),
                    }


        st.session_state.analysis_running = True
        st.session_state.analysis_complete = False
        st.session_state.analysis_error = None
        st.session_state.pending_result = None

        thread = threading.Thread(target=_run_analysis, daemon=True)
        thread.start()
        st.rerun()

    # ── 未配置 API Key 的提示 ─────────────────────────────────────
    if not settings.has_api_key:
        st.warning(
            "⚠️ **未配置 API Key**\n\n"
            "请在项目根目录创建 `.env` 文件，添加：\n"
            "```\nLLM_API_KEY=你的DeepSeekAPI密钥\n```",
            icon="⚠️",
        )
