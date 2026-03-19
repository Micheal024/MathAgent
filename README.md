# MathModelingAgent — 数学建模竞赛全流程智能助手

> **"思考即服务（Thinking as a Service）"** — Agent 通过自主规划和工具调用完成深度推理，用户实时观察思考过程和工具执行结果。

对标 Manus AI / OpenManus 架构，面向 MCM/ICM、CUMCM、APMCM 等数学建模竞赛的全流程 AI 辅助平台。

---

## ✨ 项目亮点

- **四阶段动态规划工作流**：破题分析 → 建模设计 → 代码实现 → 论文撰写，每阶段步骤由 LLM 基于题目动态生成
- **Obs→Eval→Fix 自修复内循环**：Coding 阶段最多 3 次迭代自动修复代码，质量有保证
- **双层记忆系统（memU 启发）**：短期/长期记忆分层管理，LLM 阶段综合，上下文永不溢出
- **实时思考可视化**：WebSocket 推送 Agent 思考链、工具调用、阶段进度，全程透明可观测
- **多 LLM Provider 支持**：统一 OpenAI-Compatible 接口，支持 GPT-4o、DeepSeek、通义千问、豆包等
- **沙箱三级降级**：OpenSandbox → E2B → 本地持久命名空间，开发无需云端环境
- **前端零构建**：纯 HTML/CSS/Vanilla JS，CDN 加载依赖，无需 Node.js

---

## 📸 界面预览

> 前端采用暗色主题，支持中英文双语切换，实时展示 Agent 思考过程与阶段进度。

---

## 🏗 系统架构

```
用户 (Browser)
    ↓ WebSocket + REST API
FastAPI Server (port 8000)
    ├── REST API  (/api/v1/projects · /chat · /workflow · /artifacts · /upload)
    └── WebSocket (/ws/project/{project_id})
            ↓ 消息调度
    PlanningFlow（四阶段编排核心）
        ├── Phase 1: Inception     — 破题与分析
        ├── Phase 2: Blueprinting  — 建模方案设计
        ├── Phase 3: Coding        — 代码实现（含 Obs→Eval→Fix 内循环）
        └── Phase 4: Writing       — 论文撰写与合规检查
            ↓ 每阶段结束自动综合
    MemoryManager（双层记忆协调）
        ├── ShortTermMemory — 会话级，≤6000 字/阶段
        └── LongTermMemory  — 项目级，持久化，LLM 综合写入
```

---

## 🛠 技术栈

### 后端

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| AI Agent 框架 | Camel AI |
| LLM SDK | OpenAI-Compatible（支持多 Provider） |
| 数据库 | SQLite（开发）/ PostgreSQL + pgvector（生产） |
| 缓存 / 任务队列 | Redis + Celery |
| 代码沙箱 | OpenSandbox / E2B / 本地子进程 |
| PDF 解析 | PyMuPDF |
| 认证 | JWT（python-jose + passlib） |
| 日志 | Loguru |
| 代码检查 | Ruff |

### 前端

| 类别 | 技术 |
|------|------|
| 框架 | 原生 Vanilla JS（无构建工具） |
| Markdown 渲染 | Marked.js |
| 代码高亮 | Prism.js |
| 数学公式 | KaTeX |
| 实时通信 | WebSocket（浏览器原生 API） |

### 支持的 LLM Provider

| Provider | 默认模型 |
|----------|---------|
| OpenAI（默认） | gpt-4o |
| DeepSeek | deepseek-chat |
| 通义千问 | qwen-max |
| 豆包 | doubao-pro-32k |
| MiniMax | abab6.5-chat |

---

## 🤖 Agent 工具集

| 工具 | 功能描述 |
|------|---------|
| `python_execute` | 在沙箱中执行 Python（支持 numpy/scipy/pandas/matplotlib/sklearn/pytorch） |
| `search_literature` | 搜索 Semantic Scholar 学术论文 |
| `classify_problem` | 分析竞赛题型（优化 / 预测 / 评价 / 模拟） |
| `query_math_kg` | 查询数学建模知识图谱，推荐算法与模型 |
| `ask_human` | Gate 节点向用户提问，等待用户决策 |
| `str_replace_editor` | 创建 / 编辑代码或文档文件 |
| `planning` | 创建 / 更新任务执行计划 |
| `latex_compile` | 编译 LaTeX 源码为 PDF（xelatex 双遍） |
| `compliance_check` | 检查论文合规性（页数 / 禁词 / 引用 / AI 声明） |
| `file_parser` | 解析上传的 PDF / 图片竞赛题 |
| `terminate` | 任务完成后发出终止信号 |

---

## 📁 项目结构

```
graduatework/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 多层配置管理
│   │   ├── agent/              # Agent 工厂
│   │   ├── flow/               # PlanningFlow 四阶段编排
│   │   ├── tool/               # 11 种专业工具
│   │   ├── prompt/             # 系统提示词 & 动态 Prompt
│   │   ├── memory/             # 双层记忆系统
│   │   ├── api/                # REST API 路由
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   └── ws/                 # WebSocket 处理器
│   ├── config/
│   │   └── config.example.toml
│   ├── tests/
│   ├── docker-compose.yml      # Postgres + Redis
│   ├── pyproject.toml
│   └── requirements.txt
├── front/                      # 纯静态前端
│   ├── index.html
│   ├── app.js                  # UI 渲染 & 哈希路由
│   ├── ws.js                   # WebSocket 客户端
│   ├── api.js                  # REST 客户端
│   └── styles.css
├── docs/                       # 产品文档 & 设计文档
├── memory/                     # Agent 记忆文档
└── README.md
```

---

## 🚀 快速开始

### 环境要求

- Python ≥ 3.11
- （可选）Docker & Docker Compose（生产模式 Postgres/Redis）

### 1. 克隆仓库

```bash
git clone git@github.com:Micheal024/graduatework.git
cd graduatework
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `.env`，填入必要配置：

```ini
# LLM 配置（必填）
LLM_MODEL=gpt-4o
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.0

# 数据库（默认 SQLite，开发无需 Docker）
DB_URL=sqlite+aiosqlite:///./mathagent.db

# 代码沙箱（三选一：opensandbox / e2b / local）
SANDBOX_PROVIDER=local

# 认证密钥
AUTH_SECRET_KEY=your-secret-key-here
```

### 3. 安装依赖并启动后端

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. 启动前端

直接用浏览器打开 `front/index.html`，或启动本地静态服务器：

```bash
python -m http.server 5173 -d front/
# 访问 http://localhost:5173
```

### 生产模式（PostgreSQL + Redis）

```bash
cd backend
docker compose up -d            # 启动 Postgres + Redis
# 修改 .env 中 DB_URL 为 postgresql+asyncpg://...
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📡 WebSocket 通信协议

### 客户端 → 服务端

| 消息类型 | 说明 |
|---------|------|
| `user_message` | 发送新任务或对话消息 |
| `human_response` | 回复 AskHuman Gate 节点的提问 |
| `phase_confirm` | 确认进入下一阶段 |
| `stop` | 取消当前执行 |

### 服务端 → 客户端

| 事件类型 | 说明 |
|---------|------|
| `thought` | Agent 实时思考过程 |
| `assistant_message` | 最终回复内容 |
| `ask_human` | 请求用户输入（Gate 节点） |
| `phase_start` / `phase_complete` | 阶段开始 / 完成 |
| `step_start` / `step_complete` | 步骤执行状态 |
| `eval_step` | Obs→Eval→Fix 内循环状态 |
| `artifact_saved` | 制品（报告/代码/论文）已保存 |
| `tool_call` | 工具调用通知 |
| `error` | 错误消息 |

---

## 🎯 目标用户与应用场景

**目标用户**

- 参加 MCM/ICM、CUMCM、APMCM、IMMC 等赛事的大学生 / 研究生
- 高校数学建模课程教师与竞赛指导教师

**核心场景**

在 72–96 小时的数学建模竞赛中实现全流程 AI 辅助：

1. 上传竞赛题（PDF / 图片 / 文本）→ 自动结构化解析
2. AI 生成解题策略，Gate 节点等待用户确认
3. 自动编写 Python 代码并在沙箱中验证（含自修复）
4. 撰写符合竞赛规范的 LaTeX 论文并自动合规检查

**核心价值指标**

| 指标 | 传统方式 | 使用本系统 |
|------|---------|-----------|
| 破题时间 | ~2 小时 | ~15 分钟 |
| 编码效率 | 基准 | 提升 50% |
| 论文格式合规率 | 不稳定 | 100% |

---

## 🧪 运行测试

```bash
cd backend
pytest tests/ -v
```

---

## 📄 许可证

本项目为毕业设计研究项目，仅供学习与研究使用。

---

## 🙏 致谢

- [Camel AI](https://github.com/camel-ai/camel) — Agent 框架
- [OpenManus](https://github.com/mannaandpoem/OpenManus) — 架构参考
- [Semantic Scholar](https://www.semanticscholar.org/) — 学术文献搜索 API
- [E2B](https://e2b.dev/) — 云端代码沙箱
"# MathAgent" 
