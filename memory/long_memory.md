# MathModelingAgent — 项目长期记忆 (Long Memory)

> 本文档详细记录项目的完整架构、模块职责、数据流、配置方式和开发约定。
> 供任何 AI 模型、IDE 插件或新开发者深入理解项目全貌。

---

## 1. 项目概述

**MathModelingAgent** 是一个 AI 驱动的全流程数学建模助手，面向 MCM/ICM/CUMCM/APMCM 等数学建模竞赛。系统自动化完成从题目分析、方案设计、代码实现到论文生成的完整流程。

**核心灵感来源**：Manus / OpenManus 架构 — 多阶段 Agent 编排 + 工具调用 + 人机交互；memU — 双层记忆管理（短期工作缓冲 + 长期重要性知识库）。

---

## 2. 目录结构

```
math/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # FastAPI 入口 (lifespan, CORS, 路由注册)
│   │   ├── config.py        # 全局配置 (LLM/DB/Sandbox/Auth)
│   │   ├── context.py       # ContextVar: project_id 线程级变量
│   │   ├── camel_compat.py  # CAMEL AI 兼容层 (绕过 import 问题)
│   │   ├── interaction.py   # InteractionManager: Agent↔用户同步通信桥
│   │   ├── schema.py        # 核心枚举和数据结构 (AgentState, Plan, PlanStep)
│   │   ├── agent/
│   │   │   └── math_modeling.py  # ChatAgent 工厂 (planning_agent + executor_agent)
│   │   ├── flow/
│   │   │   ├── base.py           # BaseFlow 抽象基类
│   │   │   └── planning.py       # PlanningFlow: 四阶段编排引擎 + MemoryManager 集成 (核心)
│   │   ├── memory/               # 双层记忆系统 (新增)
│   │   │   ├── __init__.py       # 包入口: 导出 ShortTermMemory, LongTermMemory, MemoryManager
│   │   │   ├── short_term.py     # ShortTermMemory: 有界会话缓冲
│   │   │   ├── long_term.py      # LongTermMemory: 重要性评分持久化
│   │   │   └── manager.py        # MemoryManager: 协调两层 + LLM 综合
│   │   ├── prompt/
│   │   │   └── math_modeling.py  # 系统提示词 + 四阶段提示词
│   │   ├── tool/                 # 10 个 Agent 工具
│   │   │   ├── base.py           # ToolRegistry 工具注册器
│   │   │   ├── terminate.py      # 终止执行
│   │   │   ├── python_execute.py # 代码执行 (OpenSandbox/E2B/本地，三级降级)
│   │   │   ├── ask_human.py      # 询问用户 (Gate 机制)
│   │   │   ├── str_replace_editor.py  # 文件创建/编辑/查看
│   │   │   ├── planning.py       # 计划管理 (create/list/mark/update)
│   │   │   ├── search_literature.py   # 文献检索 (Semantic Scholar)
│   │   │   ├── classify_problem.py    # 题目分类
│   │   │   ├── query_math_kg.py       # 数学建模知识图谱
│   │   │   ├── latex_compile.py       # LaTeX → PDF 编译
│   │   │   ├── compliance_check.py    # 论文合规性检查
│   │   │   └── file_parser.py         # 文件解析 (PDF/图片/文本)
│   │   ├── api/                  # REST API 路由
│   │   │   ├── projects.py       # CRUD /api/v1/projects
│   │   │   ├── chat.py           # GET /api/v1/project/{id}/history
│   │   │   ├── artifacts.py      # GET /api/v1/artifacts/{id}
│   │   │   ├── upload.py         # POST /api/v1/upload/
│   │   │   └── workflow.py       # (占位)
│   │   ├── models/               # SQLAlchemy ORM
│   │   │   ├── database.py       # Engine + async_session
│   │   │   ├── user.py           # User
│   │   │   └── project.py        # Project, AgentSession, ChatLog, Artifact,
│   │   │                         # MemoryItem (长期记忆), ShortTermMemoryEntry (短期记忆)
│   │   ├── schemas/
│   │   │   └── __init__.py       # Pydantic 请求/响应模型
│   │   └── ws/
│   │       └── handler.py        # WebSocket 端点 + 停止/恢复逻辑
│   ├── .env / .env.example       # 环境变量
│   ├── requirements.txt          # Python 依赖
│   ├── pyproject.toml            # 包元数据
│   └── mathagent.db              # SQLite 数据库文件
├── front/                   # 纯静态前端
│   ├── index.html           # 入口 (CDN: marked, prism, katex)
│   ├── app.js               # SPA 主逻辑 (~1500 行)
│   ├── ws.js                # WebSocket 客户端类
│   ├── api.js               # REST API 客户端 (带 5s 超时)
│   └── styles.css           # 全部样式 (~1100 行)
├── docs/                    # 需求文档
│   ├── PRD.md               # 产品需求文档
│   └── 数学建模.md           # 数学建模领域参考
├── memory/                  # 项目记忆 (本文件所在位置)
│   ├── short_memory.md      # 快速参考
│   └── long_memory.md       # 详细文档 (本文件)
└── papers/                  # 参考文献
```

---

## 3. 核心架构详解

### 3.1 PlanningFlow — 四阶段编排引擎

**文件**: `backend/app/flow/planning.py`

这是整个系统的**大脑**。它将一次建模任务分解为 4 个阶段，每个阶段先用 `planning_agent` 生成步骤计划，再用 `executor_agent` 逐步执行。

```
PlanningFlow.execute(input_text)
  ├── Phase 1: INCEPTION (破题分析)
  │   ├── memory.start_phase("inception")     ← 清空短期记忆
  │   ├── planning_agent → 生成步骤 (1. 2. 3. ...)
  │   ├── executor_agent → 逐步执行 (使用工具)
  │   │   └── 每步: memory.build_step_context() → 执行 → memory.record_step()
  │   └── memory.synthesize_phase() → LLM 生成综合报告 (长期记忆 importance=2.0)
  ├── Phase 2: BLUEPRINTING (建模方案)  [同上]
  ├── Phase 3: CODING (代码实现)        [同上]
  └── Phase 4: WRITING (论文撰写)       [同上]
```

**关键特性**:
- 每个 phase 重置 Agent 对话历史以控制 token 消耗
- 通过 `MemoryManager` 在阶段间传递高质量综合上下文（取代原始字符串截断）
- 支持 API 额度中断后恢复（快照机制）

### 3.2 双层记忆系统 (Two-Tier Memory)

**目录**: `backend/app/memory/`

灵感来自 [memU 架构](https://github.com/NevaMind-AI/memU-server)，将短暂的工作记忆与持久化的知识库分离。

#### 短期记忆 (ShortTermMemory)

**文件**: `backend/app/memory/short_term.py`

| 属性 | 值 |
|------|-----|
| 范围 | 会话 (session_id) + 阶段 (phase) |
| 容量 | 最大 6000 字符/阶段槽 |
| 溢出策略 | FIFO — 删除最旧的条目直到低于上限 |
| 生命周期 | 阶段切换时调用 `clear_phase()` 主动清空 |
| 检索方式 | 按时序倒序（最近步骤优先），截断到 `max_chars` |

```python
st = ShortTermMemory(project_id, session_id)
await st.add(content, phase="inception")          # 写入，自动淘汰
await st.get_window(phase="inception", max_chars=2200)  # 读取最近步骤
await st.clear_phase("inception")                 # 阶段切换时调用
```

**存储表**: `short_term_memory` (`ShortTermMemoryEntry` ORM)

#### 长期记忆 (LongTermMemory)

**文件**: `backend/app/memory/long_term.py`

| 属性 | 值 |
|------|-----|
| 范围 | 项目 (project_id) |
| 生命周期 | 跨会话持久化 |
| 检索方式 | 结构化（按 phase + content_type）+ 关键词重叠 × 重要性评分 |

**重要性评分表**:
```
synthesis     = 2.0  ← LLM 阶段综合报告（最高价值）
user_decision = 1.8  ← 用户 AskHuman 决策（明确意图）
key_finding   = 1.5  ← 关键发现
conclusion    = 1.3  ← 结论
result        = 1.0  ← 普通步骤结果
analysis      = 1.0  ← 分析
code          = 0.8  ← 代码（信噪比低）
```

**核心方法**:
```python
lt = LongTermMemory()
await lt.remember_step(project_id, phase, step_index, step_title, content)  # 存步骤
await lt.recall_by_phase(project_id, phase)                                  # 取阶段所有步骤
await lt.build_phase_context(project_id, current_phase, max_chars=2000)      # 前序阶段综合
await lt.build_step_context(project_id, current_phase, step_index, max_chars)# 步骤执行上下文
```

**存储表**: `memory_items` (`MemoryItem` ORM)

#### MemoryManager — 协调器

**文件**: `backend/app/memory/manager.py`

`PlanningFlow` 唯一的记忆入口，向上屏蔽两层细节：

```python
memory = MemoryManager(executor_agent, project_id, session_id)

# 阶段生命周期
await memory.start_phase("inception")                         # 清空短期记忆

# 步骤存储
await memory.record_step("inception", 0, "分析题目", result)  # 同时写两层

# 上下文窗口构造
ctx = await memory.build_step_context("inception", 1)         # 组合长短期上下文
plan_ctx = await memory.build_planning_context("blueprinting") # 规划时专用

# 阶段综合
synthesis = await memory.synthesize_phase("inception")        # LLM 生成综合报告
```

**上下文窗口结构**:
```
## 长期记忆（跨阶段知识）
### 【Inception 综合】
[上一阶段 LLM 综合报告节选...]

## 短期记忆（当前阶段步骤）
[step_result] 步骤 1 [分析题目]:
[本阶段已完成步骤...]
```

**LLM 综合流程**:
1. 从 `LongTermMemory` 加载阶段所有非 synthesis 条目
2. 构建阶段专属 prompt（每个 phase 一套中文模板）
3. 调用 `executor_agent.step()` —— 调用前后各 `reset()` 避免污染上下文
4. 将结果以 `importance=2.0` 写入 `LongTermMemory`

### 3.3 双 Agent 架构

| Agent | 角色 | 有工具? |
|-------|------|---------|
| `planning_agent` | 将任务分解为可执行步骤 | ❌ 纯文本输出 |
| `executor_agent` | 使用工具执行每个步骤；复用于 MemoryManager 综合 | ✅ 10 个工具 |

**工厂函数**: `backend/app/agent/math_modeling.py`
- `create_planning_agent()` → 无工具 ChatAgent
- `create_math_modeling_agent()` → 带完整工具集的 ChatAgent

### 3.4 LLM 配置与多提供商

**文件**: `backend/app/config.py`

通过 `.env` 配置切换不同 LLM 提供商：

```env
LLM_PROVIDER=minimax    # openai | deepseek | minimax | qwen | doubao
LLM_MODEL=abab6.5-chat
LLM_BASE_URL=https://api.minimax.chat/v1
LLM_API_KEY=your-key
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.0

# 代码沙箱配置
SANDBOX_PROVIDER=opensandbox          # "opensandbox" | "e2b" | "local"
SANDBOX_OPENSANDBOX_DOMAIN=localhost:8080
SANDBOX_OPENSANDBOX_API_KEY=
SANDBOX_OPENSANDBOX_IMAGE=opensandbox/code-interpreter:v1.0.1
SANDBOX_E2B_API_KEY=
SANDBOX_TIMEOUT_SECONDS=30
```

所有提供商都通过 **OpenAI 兼容接口** (CAMEL AI 的 `OPENAI_COMPATIBLE_MODEL`)。无有效 API Key 时自动降级为 CAMEL 的 `STUB` 模型。

---

## 4. 工具系统详解

所有工具定义在 `backend/app/tool/` 下，通过 `ToolRegistry` 注册为 CAMEL AI 的 `OpenAIFunction`。

| # | 工具 | 功能 | 关键依赖 |
|---|------|------|----------|
| T1 | `python_execute` | 在沙箱中执行 Python 代码 | OpenSandbox / E2B / subprocess（三级降级）|
| T3 | `str_replace_editor` | 创建/编辑/查看工作区文件 | 本地文件系统 |
| T4 | `search_literature` | 学术文献检索 | Semantic Scholar API |
| T5 | `classify_problem` | 分析题目类型和结构 | LLM 推理 |
| T6 | `query_math_kg` | 查询内置数学建模知识库 | 本地知识图谱 |
| T7 | `latex_compile` | LaTeX → PDF 编译 | xelatex |
| T8 | `compliance_check` | 论文合规性报告 | 规则库 (MCM/ICM/CUMCM/APMCM) |
| T9 | `ask_human` | 暂停执行等待用户输入 | InteractionManager |
| T10 | `terminate` | 终止 Agent 执行 | — |
| T11 | `planning` | 管理任务计划 (CRUD) | 内存中 Plan 存储 |

---

## 5. 数据模型

**文件**: `backend/app/models/`

```
User (users)
  ├── id: UUID (PK)
  ├── email, name, hashed_password, role
  └── → has_many: Project

Project (projects)
  ├── id: UUID (PK)
  ├── user_id: UUID (FK)
  ├── title, competition (MCM/ICM/CUMCM/APMCM/IMMC/other)
  ├── status (inception/blueprinting/coding/writing/completed)
  ├── shared_context: JSON
  ├── → has_many: AgentSession, ChatLog, Artifact
  ├── → has_many: MemoryItem         (长期记忆)
  └── → has_many: ShortTermMemoryEntry (短期记忆)

AgentSession (agent_sessions)
  ├── id, project_id, plan_id, plan_data, phase, started_at

ChatLog (chat_logs)
  ├── id, project_id, sender (user/agent/system)
  ├── content, msg_type (thought/code/result/gate/user_input)
  ├── metadata_json

Artifact (artifacts)
  ├── id, project_id
  ├── artifact_type (report/blueprint/code/paper)
  ├── content, version, frozen

MemoryItem (memory_items)       ← 长期记忆表
  ├── id: UUID (PK)
  ├── project_id: UUID (FK)
  ├── phase: str                 (inception/blueprinting/coding/writing)
  ├── step_index: int            (步骤序号；synthesis 条目用 9999)
  ├── step_title: str
  ├── content: Text
  ├── content_type: str          (result/synthesis/user_decision/key_finding/...)
  ├── keywords: JSON             (自动提取的关键词列表)
  ├── importance: float          (默认 1.0，synthesis=2.0)
  └── created_at: datetime

ShortTermMemoryEntry (short_term_memory)   ← 短期记忆表
  ├── id: UUID (PK)
  ├── project_id: UUID (FK)
  ├── session_id: str            (每次 WS 会话唯一 ID)
  ├── sequence_num: int          (同会话内单调递增)
  ├── phase: str
  ├── role: str                  (agent/user)
  ├── content_type: str          (step_result/thought/...)
  ├── content: Text
  ├── char_count: int            (用于容量控制)
  └── created_at: datetime
```

**数据库**: 开发默认用 SQLite (`mathagent.db`)，`.env` 中 `DB_URL` 可切换 PostgreSQL。

---

## 6. WebSocket 通信协议

**端点**: `ws://localhost:8000/ws/project/{project_id}`

### 客户端 → 服务端

| type | 描述 | payload |
|------|------|---------|
| `user_message` | 用户发送消息 | `{content: string}` |
| `stop` | 停止当前执行 | `{}` |
| `human_response` | 回复 AskHuman | `{content: string}` |

### 服务端 → 客户端

| type | 描述 |
|------|------|
| `status` | 状态更新 (Agent starting/stopped/idle) |
| `assistant_message` | Agent 最终回复 |
| `thought` | Agent 思考过程 (中间步骤日志) |
| `tool_call` | 工具调用记录 |
| `ask_human` | 需要用户确认的问题 |
| `error` | 错误信息 |
| `phase_start` | 阶段开始 (phase, phase_index) |
| `phase_plan` | 阶段计划 (step_titles) |
| `step_start` | 步骤开始 (step_index, step_title) |
| `step_complete` | 步骤完成 (result_preview) |

---

## 7. 前端架构

**纯静态 SPA**，无打包、无框架。

### 路由

| 视图 | hash | 说明 |
|------|------|------|
| 登录 | `#login` | 邮箱登录 (demo 模式，无真实验证) |
| 聊天 | `#chat` | 主工作界面 |
| 设置 | `#settings` | 主题/语言/模型配置 |

### 状态管理

全局 `state` 对象管理所有状态：

```javascript
const state = {
  currentView,           // login | chat | settings
  sidebarOpen,           // 左侧边栏
  currentProjectId,      // 当前项目 UUID
  projects: [],          // 项目列表
  messages: [],          // 聊天消息
  artifacts: [],         // 制品列表
  isConnected,           // WebSocket 连接状态
  agentStatus,           // idle | thinking | executing
  pendingFiles: [],      // 上传待发送文件
  settings: { theme, language, model, ... },
  rightPanel: { activeTab, ... },
};
```

### 右侧面板标签

| Tab | 内容 |
|-----|------|
| Timeline | 阶段/步骤进度条 |
| Code | 代码文件查看器 |
| Document | Markdown 文档预览 |
| Files | 制品文件列表 |

---

## 8. 错误恢复机制

### API 额度中断恢复

当 LLM API 返回 `429` / `rate_limit` / `quota exceeded` 等错误时：

1. `PlanningFlow._is_quota_error()` 检测到额度错误
2. `_save_snapshot()` 保存当前状态（phase、step、累积结果）
3. 向用户返回提示消息
4. 用户充值后发送 **"继续"** 等关键词
5. `handler.py` 中 `RESUME_KEYWORDS` 匹配意图
6. 调用 `flow.resume()` 从快照恢复执行

**恢复关键词**: `继续`, `接着`, `恢复`, `接着做`, `继续执行`, `continue`, `resume`, `go on`

### 停止执行

- 前端发送 `{type: "stop"}` 消息
- 后端通过 `asyncio.Task.cancel()` 取消正在运行的流程
- UI：发送按钮变为红色脉冲停止按钮

---

## 9. InteractionManager — 同步/异步桥接

**文件**: `backend/app/interaction.py`

解决核心问题：Agent 工具执行在 `run_in_executor` 的同步线程中，但 WebSocket 通信在异步事件循环中。

```
Agent 线程 (sync)              WS 事件循环 (async)
       │                              │
 ask_human() 调用               monitor_questions() 监听
       │                              │
 request_input_sync()──────────► wait_for_question()
       │ (ThreadFuture.result  ← set)  │
       │                       send "ask_human" to WS
       │                              │
       │                       用户回复  │
       │                              │
       ◄──────submit_response()────────┘
```

---

## 10. 依赖关系与版本

### 核心依赖

| 包 | 用途 |
|----|------|
| `fastapi` ≥0.115 | Web 框架 |
| `camel-ai` 0.2.89（FunctionTool API） | AI Agent 框架 |
| `opensandbox` 0.1.5 | 代码沙箱（自托管，主选） |
| `opensandbox-code-interpreter` 0.1.1 | OpenSandbox 代码执行客户端 |
| `opensandbox-server` 0.1.4 | OpenSandbox 自托管服务器 |
| `e2b-code-interpreter` 2.4.1 | 代码沙箱（云端，备选） |
| `sqlalchemy` ≥2.0 | ORM |
| `aiosqlite` ≥0.20 | 异步 SQLite |
| `openai` ≥1.60 | LLM API 客户端 |
| `httpx` ≥0.28 | HTTP 客户端 |
| `PyMuPDF` ≥1.24 | PDF 解析 |
| `Pillow` ≥10.0 | 图片处理 |

### 前端 CDN 依赖

| 库 | 版本 | 用途 |
|----|------|------|
| marked.js | 12.0.0 | Markdown 渲染 |
| Prism.js | 1.29.0 | 代码语法高亮 |
| KaTeX | 0.16.9 | LaTeX 数学公式渲染 |

---

## 11. 开发注意事项

1. **CAMEL 兼容层**: `camel_compat.py` 直接加载 `FunctionTool`（camel-ai ≥0.2.x 将 `OpenAIFunction` 改名为 `FunctionTool`，位于 `function_tool.py`）以绕过 `camel.toolkits.__init__` 的依赖问题。优先检查 `function_tool.py`（新），找不到再回退 `openai_function.py`（旧），对外统一导出为 `OpenAIFunction` 别名。修改 CAMEL 相关代码时务必注意。

2. **前端缓存**: `python3 -m http.server` 不设 Cache-Control。修改 JS/CSS 后如浏览器未更新，需在 `index.html` 的 `?v=N` 版本号 +1 或使用 `Cmd+Shift+R`。

3. **数据库**: 开发用 SQLite 文件 (`mathagent.db`)。`.env` 中 `DB_URL` 可切换 PostgreSQL (`postgresql+asyncpg://...`)。

4. **Workspace**: Agent 产出的所有文件（代码、论文、图表）存储在 `backend/workspace/` 目录下。

5. **记忆系统**: `MemoryManager` 在首个步骤时懒初始化（需要 `project_id`）。`synthesize_phase()` 在每个阶段结束后自动调用 LLM 生成综合报告，agent 在调用前后都执行 `reset()` 以避免污染执行上下文。

6. **工具执行**: 工具通过 `loop.run_in_executor` 在线程中运行（同步代码），不阻塞主事件循环。`ask_human` 工具使用 `ThreadFuture` 跨线程等待用户输入。

7. **WS 连接管理**: 每个项目 (`project_id`) 可有多个 WS 连接。`ConnectionManager` 维护连接列表并广播消息。断开后自动清理。

8. **Python 字符串注意事项**: 嵌入中文内容的 Python 字符串中，如包含双引号 `"` 字符（如 `"继续"`）需使用 Unicode 转义 `\u200c` 或改用单引号，避免语法错误。

9. **Python 版本**: 需要 Python 3.11+（`opensandbox` 包要求 `>=3.10`）。虚拟环境应用 `python@3.11` 创建：`/opt/homebrew/bin/python3.11 -m venv .venv`。

10. **OpenSandbox Server**: `python_execute` 工具默认使用 OpenSandbox，需要本地运行 `opensandbox-server`（监听 8080 端口）。Server 依赖 Docker，启动前须先启动 Docker Desktop。三级降级链：OpenSandbox → E2B（需 `SANDBOX_E2B_API_KEY`）→ 本地 subprocess。
