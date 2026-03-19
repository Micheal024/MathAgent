# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Math Modeling AI Agent — assists with MCM/ICM/CUMCM math modeling competitions. Uses a single LLM agent + planning flow architecture (inspired by OpenManus), powered by Camel AI framework.

## Commands

### Backend

```bash
cd backend

# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in LLM_API_KEY etc.
cp config/config.example.toml config/config.toml  # optional TOML config

# Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Infrastructure (Postgres + Redis, optional for dev — SQLite works by default)
docker compose up -d

# Lint
ruff check app/

# Test
pytest
pytest tests/test_foo.py -k "test_name"   # single test
```

### Frontend

No build step. Vanilla HTML/CSS/JS served as static files. Open `front/index.html` or serve with any static server on port 3000/5173 (CORS is configured for those).

## Architecture

```
backend/
  app/
    main.py            — FastAPI entry, lifespan (DB init), CORS, router mounts
    config.py          — pydantic-settings config (env prefix: LLM_, DB_, REDIS_, SANDBOX_, AUTH_, APP_)
    schema.py          — Core enums/models: AgentState, ProjectPhase, PlanStepStatus, Plan, PlanStep
    context.py         — ContextVar for request-scoped project_id
    interaction.py     — InteractionManager: bridges sync agent threads ↔ async WS handler
    camel_compat.py    — Compatibility shim to load OpenAIFunction without camel-ai eager imports
    agent/
      math_modeling.py — Factory: create_math_modeling_agent(), create_planning_agent()
    flow/
      planning.py      — PlanningFlow: 4-phase orchestration (Inception→Blueprinting→Coding→Writing)
      base.py          — Abstract BaseFlow
    tool/
      base.py          — ToolRegistry: registers Python callables as OpenAIFunction tools
      *.py             — Individual tools (python_execute, search_literature, ask_human, etc.)
    prompt/
      math_modeling.py — System prompt + per-phase prompts (Chinese)
    ws/
      handler.py       — WebSocket endpoint /ws/project/{project_id}, ConnectionManager
    api/               — REST routers: projects, chat, workflow, artifacts, upload
    models/
      database.py      — Async SQLAlchemy engine/session (SQLite dev, Postgres prod)
      project.py       — ORM: Project, AgentSession, ChatLog, Artifact
      user.py          — ORM: User
front/
  index.html           — SPA shell, loads CDN deps (Marked.js, Prism.js, KaTeX)
  app.js               — UI rendering, hash-based routing, state management
  ws.js                — AgentWebSocket class (singleton, auto-reconnect)
  api.js               — REST client hitting localhost:8000/api/v1
  styles.css           — Dark theme styles
```

## Key Patterns

- **PlanningFlow 4-phase loop**: Each phase resets both agents, asks the planning agent to decompose the task into numbered steps, then the executor agent runs each step via `ChatAgent.step()`. Accumulated context is truncated to 2000 chars between phases to stay within token limits.
- **Camel AI integration**: Agents are `camel.agents.ChatAgent` instances. Tools are registered via `ToolRegistry` which wraps plain Python functions as `OpenAIFunction`. LLM provider is configured via `ModelFactory.create()` with `OPENAI_COMPATIBLE_MODEL` platform type — supports openai, deepseek, minimax, qwen, doubao.
- **Sync/async bridge**: Camel AI's `ChatAgent.step()` is synchronous. It runs in `loop.run_in_executor()`. The `InteractionManager` uses `concurrent.futures.Future` + `asyncio.Event` to let the sync `AskHuman` tool block its thread while the async WS handler collects user input.
- **WebSocket protocol**: Client sends `{type: "user_message"|"stop"|"human_response", content}`. Server broadcasts `{type: "thought"|"assistant_message"|"status"|"ask_human"|"error"|"tool_call"|"phase_start"|"step_start"|"step_complete"|"phase_plan"|"artifact_saved", ...}`.
- **Resume on quota errors**: PlanningFlow snapshots progress when it detects rate-limit/quota errors. User can send "继续"/"continue" to resume from the checkpoint.
- **Config**: pydantic-settings loads from env vars (prefixed) and optional `config/config.toml`. Default DB is `sqlite+aiosqlite:///./mathagent.db` — no Docker needed for dev.

## Conventions

- All prompts and user-facing agent output are in Chinese (中文).
- `ruff` for linting (line-length=100, target py311).
- `pytest-asyncio` with `asyncio_mode = "auto"`.
- Dev mode uses a hardcoded demo user (`00000000-0000-0000-0000-000000000000`) — no auth required.
