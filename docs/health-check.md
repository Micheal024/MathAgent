# 项目健康检查报告

> 检查日期：2026-02-27 | 项目：MathModelingAgent v0.1.0

---

## 总体评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 安全性 | ⚠️ 3/10 | 多处硬编码密钥、无鉴权、本地代码执行无沙箱 |
| 代码质量 | 🟡 5/10 | 大量注释残留、死代码、不一致的枚举 |
| 可测试性 | 🔴 2/10 | 仅一个非标准测试脚本，无 pytest 套件 |
| 可维护性 | 🟡 5/10 | 缺少迁移、无 pyproject.toml、依赖版本松散 |
| 架构 | 🟢 7/10 | 整体分层清晰，sync/async 桥接思路正确 |

---

## 一、安全漏洞（高优先级）

### S1 — 硬编码默认密钥
**文件：** `backend/app/config.py:86`
```python
# 现状 — 危险
secret_key: str = "dev-secret-key-change-in-production"
```
**修复：** 移除默认值，强制从环境变量读取；启动时若为空则 `raise ValueError`。
```python
secret_key: str  # 无默认值，必须通过 AUTH_SECRET_KEY 环境变量注入
```

### S2 — 明文密码写入数据库
**文件：** `backend/app/api/projects.py:39`
```python
hashed_password="demo"  # 注释说 dev only，但会进生产库
```
**修复：** 即使是 demo 用户也应用 `passlib` 哈希，或完全移除该字段赋值（`User` 模型应允许 nullable）。

### S3 — 鉴权完全未启用
**文件：** `backend/app/api/projects.py:24`
```python
# user_id: uuid.UUID = Depends(get_current_user_id) # Pending auth impl
```
所有 API 端点对任何人开放。`AUTH_SECRET_KEY` 配置了但从未被校验。

**修复：** 至少在非 `APP_DEBUG=true` 时强制启用 JWT 中间件。

### S4 — 本地代码执行无隔离
**文件：** `backend/app/tool/python_execute.py:88`

`_execute_local` 直接用 `python3` 子进程执行 LLM 生成的任意代码，无 chroot/namespace/资源限制。

**修复：** 本地模式至少加 `--restricted` 或用 `subprocess` 的 `setrlimit` 限制 CPU/内存；生产必须走 E2B。

### S5 — CORS 过于宽松
**文件：** `backend/app/main.py:39-45`
```python
allow_methods=["*"],
allow_headers=["*"],
```
配合 `allow_credentials=True` 存在 CSRF 风险。

**修复：** 明确列出允许的 methods 和 headers。

---

## 二、代码质量问题

### Q1 — Pydantic v2 配置写法过时
**文件：** `backend/app/config.py`（所有子 Settings 类）

```python
# 现状 — Pydantic v1 风格
class Config:
    env_prefix = "LLM_"

# 应改为 Pydantic v2 风格
model_config = SettingsConfigDict(env_prefix="LLM_")
```

### Q2 — SQLAlchemy 同步事件挂载到异步引擎无效
**文件：** `backend/app/models/database.py:16-21`
```python
@event.listens_for(Engine, "connect")   # 监听的是同步 Engine 基类
def set_sqlite_pragma(dbapi_connection, connection_record):
```
`aiosqlite` 驱动不会触发此事件，`PRAGMA foreign_keys=ON` 实际上从未执行。

**修复：** 改用 `AsyncEngine` 的 `connect` 事件或在 `lifespan` 中显式执行 PRAGMA。

### Q3 — 枚举不一致
`schema.py` 中 `ProjectPhase` 定义了 `BLUEPRINTING`，但 `models/project.py:67` 的 `AgentSession.phase` 枚举用的是 `"strategy"`。两处不同步，会导致运行时写入失败。

### Q4 — 大段注释死代码
**文件：** `backend/app/flow/planning.py:416-428`

7 行自我矛盾的注释讨论是否要 `reset()`，最终没有结论也没有实现。应删除或转为 GitHub Issue。

### Q5 — `_build_summary` 是占位符
**文件：** `backend/app/flow/planning.py:438-439`
```python
def _build_summary(self) -> str:
    return "Execution Complete"  # Simplified
```
被 `execute()` 调用但永远返回固定字符串，导致阶段摘要无意义。

### Q6 — 方法内 import
**文件：** `backend/app/flow/planning.py:71`
```python
async def _emit(self, ...):
    import json   # 应移到文件顶部
```

### Q7 — 模块级可变类变量（竞态风险）
**文件：** `backend/app/interaction.py:15-18`
```python
class InteractionManager:
    _pending_requests: Dict[str, Tuple[str, ThreadFuture]] = {}  # 类级别共享
    _events: Dict[str, asyncio.Event] = {}
```
多个并发请求共享同一字典，且 `asyncio.Event` 在线程中创建存在线程安全问题。`future.result()` 无超时，工具调用可能永久阻塞。

**修复：** 加超时 `future.result(timeout=300)`；`asyncio.Event` 只在主事件循环中创建。

### Q8 — Unicode 转义降低可读性
**文件：** `backend/app/ws/handler.py:24`
```python
"\u7ee7\u7eed", "\u63a5\u7740", ...  # 应直接写 "继续", "接着"
```

### Q9 — 全局字典内存泄漏
**文件：** `backend/app/ws/handler.py:66-72`

`_active_tasks`、`_phase_confirm_events`、`_phase_confirm_data` 在连接异常断开时不保证清理，长期运行会积累僵尸条目。

### Q10 — `debug: bool = True` 默认开启
**文件：** `backend/app/config.py:98`

生产部署若忘记设置 `APP_DEBUG=false`，FastAPI 会暴露完整错误堆栈。

---

## 三、测试问题

### T1 — 唯一测试文件不是 pytest 测试
**文件：** `backend/tests/test_e2e_mock.py`

- 没有任何 `def test_*` 函数，pytest 无法发现它
- 用 `if __name__ == "__main__": asyncio.run(...)` 手动运行
- 硬编码绝对路径 `sys.path.append("/Users/micheal024/code/math/backend")` — 换机器即失效
- 裸 `except: pass`（第 59 行）吞掉所有异常
- 用原始 SQL 字符串查询（第 111 行）而非 SQLAlchemy `text()`
- Mock 返回值 `([msg], False, {})` 是元组，但 `ChatAgent.step()` 返回 `ChatAgentResponse` 对象 — mock 本身是错的

**修复方向：**
```python
# 改为标准 pytest-asyncio 测试
import pytest

@pytest.mark.asyncio
async def test_flow_creates_artifacts():
    ...
```

### T2 — 测试覆盖率接近零
- 无单元测试（工具函数、schema、config）
- 无 API 集成测试（用 `httpx.AsyncClient`）
- 无 WebSocket 测试

---

## 四、依赖与工程化

### D1 — 缺少 Alembic 迁移
`requirements.txt` 包含 `alembic>=1.14.0`，但项目中没有 `alembic/` 目录和 `env.py`。当前用 `create_all` 建表，生产环境无法做增量迁移。

**修复：**
```bash
cd backend && alembic init alembic
# 配置 env.py 使用 async engine
alembic revision --autogenerate -m "initial"
```

### D2 — 无 `pyproject.toml`
现代 Python 项目应用 `pyproject.toml` 统一管理：包元数据、ruff 配置、pytest 配置、mypy 配置。当前这些分散或缺失。

### D3 — 依赖版本过松
```
camel-ai>=0.1.6        # 核心依赖，minor 版本 breaking change 风险极高
fastapi>=0.115.0       # 可接受
celery>=5.4.0          # 未使用，应移除
redis>=5.2.0           # 未使用（无 Celery 任务），应移除
pgvector>=0.3.6        # 未使用，应移除
```

**修复：** 用 `pip-compile`（pip-tools）或 `uv lock` 生成锁文件；移除未使用依赖。

### D4 — Python 版本不匹配
`.venv` 是 Python 3.9，但 `CLAUDE.md` 和 ruff 配置写的是 `target py311`。`match` 语句等 3.10+ 特性在 3.9 下会报语法错误。

### D5 — `schemas.py` 缺失
`backend/app/api/projects.py:16` 导入 `from app.schemas import ProjectCreate, ProjectResponse`，但文件列表中没有 `app/schemas.py`（只有 `app/schema.py`）。这是一个运行时 `ImportError`。

---

## 五、前端

### F1 — 内联 SVG 字符串维护困难
`front/app.js` 开头用 JS 字符串存储所有 SVG，共 30+ 行。应改用 `<symbol>` sprite 或独立 SVG 文件。

### F2 — 无 Content Security Policy
`front/index.html` 加载多个 CDN 资源（Marked.js、Prism.js、KaTeX）但没有 CSP header，存在 XSS 风险。

### F3 — API base URL 硬编码
前端 JS 中 `localhost:8000` 硬编码，无法通过环境变量切换到生产地址。

---

## 六、优先修复清单

按风险排序：

| 优先级 | 问题 | 文件 |
|--------|------|------|
| 🔴 P0 | S1 移除硬编码 secret_key 默认值 | `config.py:86` |
| 🔴 P0 | S2 明文密码 | `api/projects.py:39` |
| 🔴 P0 | D5 `schemas.py` 缺失导致启动崩溃 | `api/projects.py:16` |
| 🔴 P0 | S4 本地代码执行无隔离 | `tool/python_execute.py` |
| 🟠 P1 | Q2 SQLite PRAGMA 未生效 | `models/database.py:16` |
| 🟠 P1 | Q3 枚举不一致 | `schema.py` vs `models/project.py` |
| 🟠 P1 | Q7 InteractionManager 竞态 + 无超时 | `interaction.py` |
| 🟠 P1 | D1 添加 Alembic 迁移 | — |
| 🟡 P2 | Q1 Pydantic v2 配置写法 | `config.py` |
| 🟡 P2 | T1/T2 补充真正的 pytest 测试 | `tests/` |
| 🟡 P2 | D3 锁定依赖版本，移除未用包 | `requirements.txt` |
| 🟡 P2 | Q4/Q5 清理死代码和占位符 | `flow/planning.py` |
| 🟢 P3 | Q8 Unicode 转义改为直接中文 | `ws/handler.py` |
| 🟢 P3 | D2 添加 `pyproject.toml` | — |
| 🟢 P3 | F3 前端 API URL 可配置化 | `front/api.js` |
