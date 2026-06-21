# 生活预演家

> 帮你预演人生的每个重要选择。

**生活预演家** 是一个 AI 驱动的决策辅助工具。当你面临"要不要裸辞""要不要分手""要不要搬家"这类人生重大决策时，它不给你标准答案，而是：

- 🔍 **拆解决策树** — 把你的纠结变成清晰的选择分支
- 🧠 **识别认知偏误** — 发现你自己没意识到的思维陷阱
- 💬 **苏格拉底式追问** — 帮你自己想清楚真正想要什么
- 🔮 **平行宇宙模拟** — 预演每个选择下 3 个月的心理轨迹（开发中）
- 📊 **数据校准** — 基于真实案例告诉你"和你相似的人怎么选"（开发中）

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 填入你的 ANTHROPIC_API_KEY
```

### 3. 启动应用

两种方式任选：

```bash
# 方式一：Streamlit 独立运行（推荐）
streamlit run ui/app.py

# 方式二：完整的 FastAPI + Streamlit
uvicorn src.api.main:app --reload
```

### 4. 打开浏览器

访问 `http://localhost:8501` 开始使用。

## 项目结构

```
life-rehearsal/
├── config/            # 配置 + LLM 提示词模板
├── src/
│   ├── models/        # Pydantic 数据模型
│   ├── core/          # 核心引擎
│   │   ├── analyzer/  # 决策分析（Phase 0）
│   │   ├── simulator/ # 模拟引擎（Phase 1-2）
│   │   ├── agents/    # 智能体系统（Phase 2）
│   │   ├── matching/  # 案例匹配（Phase 3）
│   │   └── report/    # 报告生成
│   ├── services/      # 业务编排
│   ├── api/           # FastAPI 接口
│   ├── db/            # 数据持久化
│   ├── llm/           # LLM 调用封装
│   └── utils/         # 工具函数
├── ui/                # Streamlit 前端
└── tests/             # 测试
```

## 开发路线

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 0 | 决策分析器 — LLM 分析 + 偏误检测 | 第 1-4 周 |
| Phase 1 | 单智能体模拟 — 心理状态曲线预测 | 第 5-10 周 |
| Phase 2 | 多智能体社交模拟 — 平行社会 | 第 11-18 周 |
| Phase 3 | 数据飞轮 — 反馈校准 | 第 19-24 周 |

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **AI**: Claude API (Anthropic SDK)
- **前端**: Streamlit
- **数据库**: SQLite → PostgreSQL
- **向量存储**: ChromaDB

## 隐私说明

- 所有数据默认本地存储
- 用户可完全匿名化使用
- 无需注册手机号/邮箱
