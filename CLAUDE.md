# 生活预演家 (Life Rehearsal)

> ⚠️ **CLAUDE.md 维护规则**：每次用户提出新的需求/问题、或我对代码/项目结构做了改动后，必须同步更新本文件。新增记忆写入 `C:\Users\AUSU\.claude\projects\C--Users-AUSU-Desktop-untitled3\memory\`。

AI 决策辅助工具 — 帮助用户预演人生重大决策（裸辞、分手、搬家、考研等）的后果。

## 核心定位

> "帮你思考，而非替你决定"

产品强调 **个性化**、**动态化**、**可后悔预演**。区别于知乎/职业测评等静态建议，核心差异是多智能体社会模拟引擎 + 数据飞轮校准。

## 当前阶段

**Phase 0 — 决策分析器（已完成）**：纯 LLM 分析 + 行为经济学框架，不做模拟。

未来阶段：
- **Phase 1** — 单智能体轨迹模拟（心理状态曲线 + 后悔节点预测）
- **Phase 2** — 多智能体社交模拟（平行社会推演）
- **Phase 3** — 数据飞轮与模型校准（真实反馈→模型自动调优）

## 技术栈

| 层级 | 选型 |
|------|------|
| 语言 | Python 3.11+ |
| 后端 | FastAPI (async) |
| 前端 | Streamlit 1.38+ |
| LLM SDK | OpenAI SDK (用于调用 DeepSeek API) |
| LLM 提供商 | DeepSeek (默认) / 其他 OpenAI 兼容 API |
| 数据库 | SQLite + SQLAlchemy 2.0 async |
| 图表 | Plotly |
| 配置 | pydantic-settings + .env + YAML |
| 测试 | pytest + pytest-asyncio |
| 代码规范 | ruff + mypy |

## 项目结构

```
life-rehearsal/
├── config/                  # 配置层
│   ├── settings.py          # pydantic-settings 全局配置
│   ├── __init__.py          # 包标记（重要！否则 import config 会失败）
│   ├── llm.yaml             # LLM 模型/参数/预算配置
│   ├── scenarios.yaml       # 预置决策场景模板
│   └── prompts/
│       └── analyzer.py      # ★ 所有 LLM 提示词集中管理
│
├── src/
│   ├── models/              # Pydantic 数据模型
│   │   ├── user.py          # BigFive, DecisionStyle, UserProfile
│   │   ├── decision.py      # Decision, Option, Factor, DecisionTree
│   │   ├── report.py        # AnalysisReport, BiasItem, Question
│   │   └── simulation.py    # (Phase 1+) EmotionalState, TimeSlice
│   │
│   ├── llm/                 # LLM 调用封装
│   │   ├── client.py        # LLMClient — OpenAI SDK 封装
│   │   ├── cache.py         # LLM 响应缓存
│   │   └── token_counter.py # Token 用量统计
│   │
│   ├── core/
│   │   ├── analyzer/        # ★ Phase 0 核心
│   │   │   ├── deconstructor.py   # 决策树拆解
│   │   │   ├── bias_detector.py   # 认知偏误检测 (LLM + 规则)
│   │   │   ├── style_classifier.py # 决策风格分类
│   │   │   └── questioner.py      # 苏格拉底追问
│   │   ├── report/          # 报告生成
│   │   │   ├── builder.py   # 报告构建器
│   │   │   ├── narrator.py  # 叙事化输出
│   │   │   └── visualizer.py # 图表数据生成
│   │   ├── simulator/       # (Phase 1+)
│   │   ├── agents/          # (Phase 2+)
│   │   └── matching/        # (Phase 3+)
│   │
│   ├── services/
│   │   └── decision_service.py  # ★ 分析编排（5步 pipeline）
│   │
│   ├── api/
│   │   ├── main.py          # FastAPI 入口
│   │   └── routes/
│   │       └── analyze.py   # POST /api/v1/analyze
│   │
│   ├── db/
│   │   ├── database.py      # SQLAlchemy async 连接管理
│   │   ├── models.py        # ORM 模型
│   │   └── repositories/
│   │
│   └── utils/
│       ├── logger.py        # loguru 日志
│       └── text.py          # JSON 安全解析等
│
├── ui/                      # Streamlit 前端
│   ├── app.py               # 主入口（导航 + 横幅通知）
│   ├── pages/
│   │   ├── _01_decision_input.py  # 决策输入表单 + 后台分析
│   │   ├── _02_analysis_report.py # 分析报告展示
│   │   └── _03_history.py        # 历史记录
│   └── components/
│       ├── decision_form.py
│       ├── emotional_chart.py
│       └── bias_radar.py
│
├── .env                     # API_KEY 等敏感配置
├── pyproject.toml           # 依赖管理和工具配置
└── CLAUDE.md                # 本文件
```

## 启动方式

```bash
# 安装依赖
pip install -e ".[dev]"

# 前端（Streamlit）
streamlit run ui/app.py

# 后端（FastAPI，仅用于 API 调用）
uvicorn src.api.main:app --reload
```

## 关键架构模式

### 服务 → 核心模块 → LLM 的分层结构

```
用户输入 → DecisionService (编排)
            ├── Deconstructor.deconstruct()     # Step 1: 决策树拆解
            ├── BiasDetector.detect()           # Step 2: 偏误检测 (LLM)
            ├── BiasDetector.detect_with_rule() # Step 2b: 偏误检测 (规则)
            ├── StyleClassifier.classify()      # Step 3: 风格分类
            ├── Questioner.generate()           # Step 4: 追问生成
            └── ReportBuilder.build()           # Step 5: 报告组装
                     └── build_narrative_report() # Step 6: LLM 生成叙事文本
```

每个核心模块的构造函数都接受 `llm_client=None` 参数，默认调用 `get_llm_client()` 获取单例。

### API 响应失败处理

**每个方法都返回 `(result, LLMResponse)` 元组**，调用方通过 `response.success` 判断是否成功。失败时 `result` 为 `None` 或空列表，调用方走 fallback 逻辑。

### Streamlit 后台线程模式

分析在 `threading.Thread(target=_run_analysis, daemon=True)` 中运行，不阻塞 UI。

**全局自动刷新机制**（在 `app.py` 最末尾实现）：
- 使用 `streamlit.components.v1.html` 注入 **JavaScript `setTimeout`**
- `analysis_running` 期间每 **2 秒** 自动 `window.parent.location.reload()` 一次
- 无需任何外部依赖，不占用 Python 主线程
- 无论用户在哪个页面（输入/报告/历史）都能检测到分析完成
- 分析完成后（`analysis_running` → False）JS 不再注入，刷新自动停止

完整流程：
1. 用户点「开始分析」→ 启动后台线程 → `analysis_running = True` → `st.rerun()`
2. 下次执行时检测到 `analysis_running` → 注入 `<script>setTimeout(reload, 2000)</script>`
3. 各页面显示"⏳ 后台分析中"
4. 2 秒后 JS 触发页面 reload → 重新执行脚本 → 再次注入 JS（循环）
5. 线程完成 → `analysis_complete = True`, `analysis_running = False`
6. 下次 reload 时 JS 不再注入 → 不再自动刷新 → 完成横幅出现
7. 用户选「替换」→ 跳转报告页

**之前踩过的坑**（不要重复）：
- ❌ `time.sleep(0.5); st.rerun()` 紧循环 — 阻塞主线程，页面卡死
- ❌ `streamlit_extras.autorefresh` — 新版已移除该模块
- ❌ 时间戳守卫 `if now - last >= 2.0: rerun()` — 只会触发一次，第二次执行时时间差 < 2.0

**关键注意事项**：
- `threading.Thread(daemon=True)` — 必须设为 daemon，否则进程不会退出
- ⚠️ **`st.session_state` 不能在后台线程中读写！** Streamlit 用 `threading.local()` 获取当前会话上下文，后台线程没有上下文，访问 `st.session_state` 会引发 `RuntimeError`。即使 `try/except` 也不能用——`except` 块里访问 `st.session_state` 同样会报错。
- 线程间通信改用**模块级变量 + Lock**：后台线程写入全局变量，主线程在每次脚本执行时用 `sync_thread_result()` 同步到 `st.session_state`。
- 不要在后台线程中调用任何 Streamlit UI 函数（`st.*`）。
- 错误通过 `_THREAD_RESULT["error"]` 传递，由 `sync_thread_result()` 同步到 `st.session_state.analysis_error`，在 `app.py` 中统一展示。

### Streamlit 表单持久化

表单数据存在 `st.session_state.form_data` dict 中，使用 `key=` 参数绑定 widget 值。页面切换时 widget 被卸载但 form_data 保留。读写模式：

```python
fd = st.session_state.form_data
fd["title"] = st.text_input("标题", value=fd["title"], key="input_title")
```

## 关键数据模型关系

```
DecisionCreate (用户输入)
    ↓
Decision (内部表示，含 DecisionTree)
    ↓
AnalysisService.analyze() → AnalysisResult
    ├── report: AnalysisReport
    │   ├── biases: list[BiasItem]        # 认知偏误
    │   ├── decision_style: DecisionStyleAnalysis
    │   ├── questions: list[Question]      # 追问
    │   ├── scenario_analyses: list[ScenarioAnalysis]
    │   └── key_insight: str
    ├── narrative_text: str               # LLM 生成的完整报告
    ├── llm_stats: dict
    └── timing_ms: int
```

## LLM 配置细节

### API 调用方式

使用 OpenAI SDK 调用 DeepSeek API：

```python
from openai import OpenAI
client = OpenAI(api_key="sk-xxx", base_url="https://api.deepseek.com")
```

LLMClient 封装在 `src/llm/client.py`：
- `get_llm_client()` — 获取全局单例
- `.chat(system, messages, model, ...)` — 返回 `LLMResponse`
- `.chat_json(system, messages, ...)` — 返回 `(dict | None, LLMResponse)`
- 支持缓存（语义哈希）、重试（tenacity）、token 预算控制

### 环境变量

```env
LLM_API_KEY=sk-xxx                             # DeepSeek API Key
LLM_BASE_URL=https://api.deepseek.com           # API 地址
LLM_MODEL=deepseek-chat                         # 模型名
```

### model 参数使用注意事项

`ReportBuilder.build_narrative_report()` 中调用 `self.llm.chat(..., model="claude-sonnet-4-20250514")` 是硬编码的旧值。实际使用 DeepSeek 时，不要传 model 参数（使用默认值 `deepseek-chat`）。

### 缓存策略

- 语义哈希 key: `sha256(json.dumps({system, messages, model}))`
- TTL: 3600s (配置在 `config/llm.yaml`)
- 最大条目: 1000
- 相同 prompt → 直接返回缓存，节省 API 费用

## Prompt 管理

所有 LLM prompt 集中在 `config/prompts/analyzer.py`，按功能分为 5 组：
1. `build_deconstructor_prompt` — 决策树拆解
2. `build_bias_detector_prompt` — 偏误检测
3. `build_style_classifier_prompt` — 风格分类
4. `build_questioner_prompt` — 追问生成
5. `build_report_prompt` — 叙事报告生成

每个函数返回 `(system_prompt, messages_list)` 元组。

所有 prompt 使用中文编写，输出格式要求 JSON（用 `safe_json_parse` 解析）。

## 认知偏误检测

6 种类型，在 `BiasType` 枚举中定义：

| 枚举值 | 中文名 | 说明 |
|--------|--------|------|
| LOSS_AVERSION | 损失厌恶 | 过分夸大"失去"的痛苦 |
| CONFIRMATION_BIAS | 确认偏误 | 只收集支持自己倾向的证据 |
| OVER_OPTIMISM | 过度乐观 | 低估困难概率 |
| ANCHORING | 锚定效应 | 被某个数字/经验锚定 |
| STATUS_QUO | 现状偏好 | 因为不想改变而维持现状 |
| SUNK_COST | 沉没成本 | 被已投入的成本绑架 |

检测方式：**LLM 分析 + 规则 fallback** (`detect_with_rule`)。合并时按严重度降序排列，同类型偏误保留严重度更高的。

## API 路由规范

所有后端 API 路由集中在 `src/api/routes/` 目录下，每个路由文件对应一个资源（如 `analyze.py`）。

```
src/api/
├── main.py              # FastAPI 应用入口（注册路由 + 中间件）
├── dependencies.py      # 依赖注入
├── middleware.py         # CORS / 日志中间件
└── routes/
    └── analyze.py       # POST /api/v1/analyze
```

路由函数使用类型注解 + Pydantic 模型做请求/响应校验：
```python
@router.post("/analyze", response_model=AnalyzeResponse)
async def create_analysis(input_data: DecisionCreate): ...
```

## 类型安全规范

- **所有函数参数和返回值必须有类型注解**（Python 的 `: type` 和 `-> type`），禁止裸函数
- 复杂数据结构使用 **Pydantic BaseModel** 而非 dict/tuple
- Streamlit 页面的 `render()` 函数签名统一为 `def render() -> None:`
- 事件处理函数签名统一为 `(event: EventType) -> ResultType`
- API 请求/响应使用 Pydantic model（`response_model=`），不手动构造 dict
- 使用 `from __future__ import annotations` 启用延迟求值（避免循环引用）

## HTTP 客户端

外部 HTTP 请求使用 **httpx**（已放在项目依赖中）：

```python
import httpx

async with httpx.AsyncClient() as client:
    resp = await client.get("https://api.example.com")
```

- 使用 `AsyncClient` 而非同步 `Client`（与 FastAPI async 一致）
- 配置超时：`timeout=httpx.Timeout(30.0)`
- 错误处理：捕获 `httpx.HTTPError` 并转成内部异常

## 编码规范

### Python

- 目标版本: Python 3.11+
- 行长度: 100
- 类型注解: 必须（`from __future__ import annotations` 启用延迟求值）
- import 顺序: 标准库 → 第三方 → 项目内部
- 所有文件以 `"""docstring"""` 开头
- 类和方法必须有 docstring
- 使用 `Optional[X]` 而非 `X | None`（Python 3.9 兼容风格）
- logger 使用 `src.utils.logger` 的 `logger` 实例（loguru）

### 文件命名

- 模块文件: 下划线分隔（`bias_detector.py`）
- Streamlit 页面: `_01_decision_input.py`（下划线前缀控制显示顺序）
- 测试文件: `test_<module_name>.py`

### Git

- 不要在默认分支直接提交
- commit message 结尾加 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`

## Windows 注意事项

1. **GBK 编码问题**：Windows 终端默认 GBK，读写 YAML/文件始终指定 `encoding="utf-8"`
2. **命令行 emoji**：Windows 终端可能无法显示 emoji，测试时用 ASCII
3. **路径分隔符**：使用 `Path` 对象而非字符串拼接
4. **`threading.Thread` daemon=True**：Streamlit 的分析线程必须设为 daemon，否则进程不会退出

## 性能与成本

- 单次分析 LLM 调用次数：~4 次（拆解 + 偏误 + 风格 + 追问）+ 1 次（报告生成）
- 缓存生效时：减少 ~30% API 调用
- Token 预算：50000/session （配置在 `llm.yaml`），超过后 `chat()` 返回 error 而非调用 API

## 测试

```bash
pytest tests/                    # 运行所有测试
pytest tests/ -v                 # 详细输出
pytest tests/ --cov=src          # 覆盖率报告
```

测试文件在 `tests/` 目录下，遵循 `test_<module_name>.py` 命名。

## 依赖管理

```bash
# 核心依赖
pip install -e ".[dev]"          # 安装 + 开发工具
pip install -e ".[simulation]"   # 安装 + 模拟引擎依赖（Phase 1+）
```

注意 `sentence-transformers` 和 `chromadb` 是可选依赖，它们会拉取 PyTorch (~300MB)，不要默认安装。

## 关键文件速查

| 文件 | 作用 |
|------|------|
| `ui/app.py` | Streamlit 主入口，导航栏 + 横幅通知 |
| `ui/pages/_01_decision_input.py` | 输入表单 + 后台分析线程 |
| `ui/pages/_02_analysis_report.py` | 报告展示（偏误图表 + 追问 + 选项分析） |
| `src/services/decision_service.py` | 完整 5 步分析 pipeline |
| `src/llm/client.py` | LLM 客户端（OpenAI SDK → DeepSeek） |
| `config/prompts/analyzer.py` | 所有 LLM 提示词模板 |
| `config/settings.py` | 全局配置（.env → pydantic-settings） |
| `src/models/report.py` | 分析报告数据结构 |
| `src/models/decision.py` | 决策输入数据结构 |
| `src/core/analyzer/bias_detector.py` | 偏误检测（LLM + 规则） |

## 变更记录

每次用户提出新需求或代码有改动时，在此追加记录。格式：

```
YYYY-MM-DD: 改了什么 / 用户提了什么需求
```

---

### 2026-06-09
- 创建 CLAUDE.md，规定每次用户提问或代码改动后同步更新
- 补充 API 路由规范、类型安全规范、httpx 使用规范
- Streamlit 前端三页面（输入/报告/历史）完成
- 后台分析线程 + 完成通知横幅 + 替换/丢弃流程 全部实现
- 修复 `_02_analysis_report.py` docstring 中文引号与 Python 三引号冲突的 SyntaxError
### 2026-06-10 ～ 06-11
- **Phase 1 单智能体模拟 完整实现**
  - 人格测评: `src/core/simulator/personality_quiz.py` — 12 题 BigFive（7 点李克特量表）
  - 模拟引擎: `src/core/simulator/engine.py` — 逐周 LLM 推演（两条路径各 12 周），含 clamp 保护
  - 曲线构建: `src/core/simulator/curve_builder.py` — TimeSlice → EmotionalCurve
  - Prompt 模板: `config/prompts/simulator.py` — 模拟专用 system/user prompt
  - 服务层: `src/services/simulation_service.py` — 编排完整流程
  - 新页面: `ui/pages/_04_simulation.py` — 测评→就绪→进度→结果四阶段
  - 报告底部: `ui/pages/_02_analysis_report.py` 新增「运行心理模拟」按钮
  - `app.py`: 新增导航按钮 + 路由 + fragment 监控模拟完成
  - `history_store.py`: 新增 simulations 表
  - `models/simulation.py`: 新增 SimulationResult 包装类
  - 新增 10 个文件，~1400 行代码，新增 14 个测试（共 52 passed）

- **修复后台分析慢/不分析的问题**（反复 3 次才找到根因）：
  - 第一次修复：移除 `time.sleep(0.5); st.rerun()` 紧循环 — ⚠️ 但没加替代方案，页面不再刷新
  - 第二次修复：加 `streamlit_extras.autorefresh` — ⚠️ 新版包已删除该模块
  - 第三次修复：加时间戳守卫 `if now-last>=2.0: rerun()` — ⚠️ 只会触发一次，因为第二次时时间差 < 2.0
  - **最终正确方案**：`components.html("<script>setTimeout(reload,2000)</script>")` — JS 定时器，每次 reload 重新注入，形成稳定 2 秒循环
