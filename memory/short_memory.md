# MathModelingAgent — 项目短期记忆 (Short Memory)

> 快速上手指南，供任何 AI 模型或 IDE 在 30 秒内理解本项目。

## 一句话描述

基于 **CAMEL AI + FastAPI + 纯静态前端** 的全流程数学建模 Agent，自动完成从赛题分析到论文生成。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | 纯 HTML/CSS/JS（无框架），hash 路由，WebSocket 通信 |
| 后端 | FastAPI + Uvicorn + SQLAlchemy (async) + SQLite |
| AI 引擎 | CAMEL AI ChatAgent + OpenAI 兼容 API（支持 OpenAI/DeepSeek/MiniMax/Qwen/豆包） |
| 代码沙箱 | OpenSandbox（自托管，主选）/ E2B（云端，备选）/ 本地 subprocess（降级）|
| 记忆系统 | 双层记忆：ShortTermMemory（会话级缓冲）+ LongTermMemory（重要性评分持久化） |

## 核心架构

```
用户浏览器 (localhost:3000)
  ├── api.js   → REST API 调用 (项目/历史/制品/上传)
  ├── ws.js    → WebSocket 实时通信
  └── app.js   → SPA 路由 + UI渲染

FastAPI 后端 (localhost:8000)
  ├── /api/v1/projects   → 项目 CRUD
  ├── /api/v1/upload     → 文件上传解析
  ├── /ws/project/{id}   → WebSocket 双向通信
  └── PlanningFlow        → 多阶段 Agent 编排
        ├── Phase 1: Inception (破题分析)
        ├── Phase 2: Blueprinting (建模方案)
        ├── Phase 3: Coding (代码实现)
        └── Phase 4: Writing (论文撰写)
        └── MemoryManager → 双层记忆管理
              ├── ShortTermMemory (会话级，按阶段清空)
              └── LongTermMemory  (项目级，重要性持久化)
```

## 双层记忆系统（新）

| 层级 | 类 | 范围 | 容量 | 生命周期 |
|------|-----|------|------|----------|
| 短期 | `ShortTermMemory` | 会话+阶段 | 6000字/阶段，溢出自动淘汰 | 阶段切换时清空 |
| 长期 | `LongTermMemory` | 项目 | 无上限，按重要性评分 | 跨会话持久化 |

**重要性分级（长期记忆）**:
- `synthesis` = 2.0 — 阶段综合报告（LLM 生成）
- `user_decision` = 1.8 — 用户通过 AskHuman 做出的决策
- `key_finding` = 1.5 — 关键发现
- `result` = 1.0 — 步骤执行结果（默认）

**MemoryManager 上下文窗口构造**:
```
步骤上下文 (4000 chars) =
  长期记忆 45% (跨阶段综合) + 短期记忆 55% (当前阶段最近步骤)
```

## 启动方式

```bash
# 1. 后端
cd backend
# 需要 Python 3.11+ (brew install python@3.11)
/opt/homebrew/bin/python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填入 LLM_API_KEY
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. 前端
cd front && python3 -m http.server 3000
```

## 关键文件速查

| 文件 | 作用 |
|------|------|
| `backend/app/main.py` | FastAPI 入口，注册路由 |
| `backend/app/config.py` | 多 LLM 提供商配置 |
| `backend/app/agent/math_modeling.py` | ChatAgent 工厂 + 工具注册 |
| `backend/app/flow/planning.py` | **核心**：4阶段 PlanningFlow 编排 + MemoryManager 集成 |
| `backend/app/memory/__init__.py` | 记忆包入口 |
| `backend/app/memory/short_term.py` | ShortTermMemory：有界会话缓冲 |
| `backend/app/memory/long_term.py` | LongTermMemory：重要性评分持久化 |
| `backend/app/memory/manager.py` | MemoryManager：双层记忆协调器 |
| `backend/app/ws/handler.py` | WebSocket 处理 + 停止/恢复逻辑 |
| `backend/app/tool/*.py` | 10 个 Agent 工具 |
| `front/app.js` | 前端 SPA 全部逻辑 (~1500行) |
| `backend/app/camel_compat.py` | camel-ai 版本兼容层（OpenAIFunction→FunctionTool 适配）|

## 当前状态

- ✅ 四阶段 Agent 流程可运行
- ✅ 双层记忆系统（ShortTermMemory + LongTermMemory + MemoryManager）
- ✅ 阶段 LLM 综合报告（synthesis，不再是步骤原始拼接）
- ✅ 跨阶段上下文自动传递（通过 LongTermMemory 综合）
- ✅ 文件上传（PDF/图片/文本）
- ✅ 停止对话功能
- ✅ API 额度中断后恢复（发送"继续"）
- ✅ Timeline 每个步骤 result 默认展开显示
- ✅ Timeline 持久化：刷新后恢复
- ✅ 删除项目功能：hover 显示删除按钮，DELETE /api/v1/projects/{id}
- ✅ OpenSandbox 沙箱接入（alibaba/OpenSandbox，自托管）
- ✅ camel-ai 0.2.89 兼容（FunctionTool + OPENAI_COMPATIBLE_MODEL）
- ✅ Python 3.11 虚拟环境（需 Homebrew python@3.11）
- ⚠️ OpenSandbox Server 需要 Docker 运行（Docker Desktop 尚未安装）
- ⚠️ 认证未实现（使用 demo 用户）
- ⚠️ 前端使用 `python3 -m http.server`（需 cache-busting `?v=N`）
