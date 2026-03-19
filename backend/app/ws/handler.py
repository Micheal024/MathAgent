"""WebSocket connection manager and handler.

Manages real-time connections for streaming agent thoughts and tool outputs.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.agent.math_modeling import create_math_modeling_agent, create_planning_agent
from app.flow.planning import PlanningFlow
from passlib.context import CryptContext

ws_router = APIRouter()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Keywords that signal the user wants to resume an interrupted flow
RESUME_KEYWORDS = {
    "continue", "resume", "go on",
    "继续", "接着", "恢复", "接着做", "继续执行",
}


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        # active_connections: {project_id: List[WebSocket]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        logger.info(f"WS connected: project_id={project_id}")

    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        logger.info(f"WS disconnected: project_id={project_id}")

    async def broadcast(self, message: dict, project_id: str):
        """Send a message to all clients connected to a project."""
        if project_id not in self.active_connections:
            return

        payload = json.dumps(message, ensure_ascii=False)
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"WS send error: {e}")


manager = ConnectionManager()

# Per-project active flow instances (for resume support)
_project_flows: Dict[str, "PlanningFlow"] = {}

# Track active execution tasks per project for cancellation
_active_tasks: Dict[str, asyncio.Task] = {}
_phase_confirm_events: Dict[str, asyncio.Event] = {}

# Track pending phase_complete data per project so we can re-send on reconnect
_phase_confirm_data: Dict[str, dict] = {}  # {project_id: {phase, summary}}


def get_project_runtime_state(project_id: str) -> dict:
    """Return a serialisable snapshot of runtime state for a project."""
    task = _active_tasks.get(project_id)
    flow = _project_flows.get(project_id)
    return {
        "status": "running" if task and not task.done() else "idle",
        "connected_clients": len(manager.active_connections.get(project_id, [])),
        "has_active_flow": flow is not None,
        "can_resume": bool(flow and flow.can_resume),
        "waiting_for_phase_confirm": project_id in _phase_confirm_events,
    }


async def stop_project_execution(project_id: str) -> bool:
    """Cancel a running project task if it exists."""
    task = _active_tasks.get(project_id)
    if not task or task.done():
        return False

    task.cancel()
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=2.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    return True


def _drop_finished_flow(project_id: str) -> None:
    """Release flow state once there is nothing left to resume."""
    flow = _project_flows.get(project_id)
    if not flow:
        return
    if flow.can_resume:
        return
    if _active_tasks.get(project_id) and not _active_tasks[project_id].done():
        return
    if project_id in _phase_confirm_events:
        return
    _project_flows.pop(project_id, None)


@ws_router.websocket("/ws/project/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for agent interaction."""
    # Validate UUID
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        await websocket.close(code=4000, reason="Invalid UUID")
        return

    # Ensure Project Exists
    from app.models.database import async_session
    from app.models.project import Project
    from app.models.user import User
    
    async with async_session() as session:
        project = await session.get(Project, project_uuid)
        if not project:
            # Create default user if needed
            default_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
            user = await session.get(User, default_user_id)
            if not user:
                user = User(
                    id=default_user_id,
                    email="demo@example.com",
                    name="Demo User",
                    hashed_password=_pwd_context.hash("demo"),
                    role="student"
                )
                session.add(user)
                await session.flush()
            
            project = Project(
                id=project_uuid,
                user_id=user.id,
                title="Demo Project",
                competition="MCM"
            )
            session.add(project)
            await session.commit()
            logger.info(f"Created new project: {project_id}")

    await manager.connect(websocket, project_id)

    # Re-send phase_complete if backend is still waiting for confirmation on this project
    if project_id in _phase_confirm_events and project_id in _phase_confirm_data:
        pending = _phase_confirm_data[project_id]
        payload = {
            "type": "phase_complete",
            "content": json.dumps(pending),
        }
        try:
            await websocket.send_json(payload)
            logger.info(f"Re-sent pending phase_complete for project {project_id}")
        except Exception as e:
            logger.error(f"Failed to re-send phase_complete: {e}")
    
    # Initialize InteractionManager loop if not set
    from app.interaction import InteractionManager
    if not InteractionManager._loop:
        InteractionManager.set_loop(asyncio.get_running_loop())

    # Helper to stream output AND persist to DB
    async def stream_output(msg_type: str, content: str, **kwargs):
        # 1. Send to WS
        payload = {"type": msg_type, "content": content, **kwargs}
        await manager.broadcast(payload, project_id)

        # Track phase_complete data for reconnect re-send
        if msg_type == "phase_complete":
            try:
                data = json.loads(content) if isinstance(content, str) else content
                _phase_confirm_data[project_id] = {
                    "phase": data.get("phase") or kwargs.get("phase", ""),
                    "summary": data.get("summary") or kwargs.get("summary", ""),
                }
            except Exception:
                _phase_confirm_data[project_id] = {
                    "phase": kwargs.get("phase", ""),
                    "summary": kwargs.get("summary", ""),
                }

        # Filter ephemeral / high-frequency events from DB persistence
        if msg_type in ("status", "eval_step", "memory_update"):
            return

        # 2. Persist timeline events to shared_context
        if msg_type in ("phase_plan", "step_complete", "phase_complete"):
            try:
                from app.models.database import async_session
                from app.models.project import Project
                from sqlalchemy import select
                async with async_session() as session:
                    result = await session.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
                    proj = result.scalars().first()
                    if proj:
                        ctx = dict(proj.shared_context) if proj.shared_context else {}
                        timeline = ctx.get("timeline", [])
                        if msg_type == "phase_plan":
                            data = json.loads(content) if isinstance(content, str) else content
                            phase_name = data.get("phase") or kwargs.get("phase", "")
                            step_titles = data.get("step_titles") or kwargs.get("step_titles", [])
                            # Add phase if not exists
                            if not any(p["name"] == phase_name for p in timeline):
                                timeline.append({
                                    "name": phase_name,
                                    "status": "running",
                                    "steps": [{"title": t, "status": "pending", "result": ""} for t in step_titles]
                                })
                            else:
                                for p in timeline:
                                    if p["name"] == phase_name:
                                        p["steps"] = [{"title": t, "status": "pending", "result": ""} for t in step_titles]
                        elif msg_type == "step_complete":
                            data = json.loads(content) if isinstance(content, str) else content
                            phase_name = data.get("phase") or kwargs.get("phase", "")
                            step_index = data.get("step_index") if data.get("step_index") is not None else kwargs.get("step_index")
                            result_preview = data.get("result_preview") or kwargs.get("result_preview", "")
                            for p in timeline:
                                if p["name"] == phase_name:
                                    if step_index is not None and step_index < len(p["steps"]):
                                        p["steps"][step_index]["status"] = "completed"
                                        p["steps"][step_index]["result"] = result_preview
                                    # Mark phase completed if all steps done
                                    if all(s["status"] == "completed" for s in p["steps"]):
                                        p["status"] = "completed"
                        elif msg_type == "phase_complete":
                            # Persist the phase confirm state to DB so it survives reconnects
                            data = json.loads(content) if isinstance(content, str) else content
                            phase_name = data.get("phase") or kwargs.get("phase", "")
                            summary = data.get("summary") or kwargs.get("summary", "")
                            ctx["phase_confirm"] = {"phase": phase_name, "summary": summary}
                        ctx["timeline"] = timeline
                        proj.shared_context = ctx
                        await session.commit()
            except Exception as e:
                logger.error(f"Failed to save timeline: {e}")

        # 3. Save to DB
        try:
            from app.models.database import async_session
            from app.models.project import ChatLog
            
            db_msg_type = "thought" # default
            if msg_type == "assistant_message":
                db_msg_type = "result" 
            elif msg_type == "user_message":
                db_msg_type = "user_input"
            elif msg_type == "ask_human":
                db_msg_type = "gate"
            elif msg_type == "tool_call":
                db_msg_type = "code" # Map tool calls to code/thought
            elif msg_type == "error":
                db_msg_type = "result" # Log errors as results for visibility

            async with async_session() as session:
                log_entry = ChatLog(
                    project_id=uuid.UUID(project_id) if isinstance(project_id, str) else project_id,
                    sender="user" if msg_type == "user_message" else "agent",
                    content=str(content),
                    msg_type=db_msg_type,
                    metadata_json=kwargs
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save chat log: {e}")

    # Background task to monitor for questions from AskHuman tool
    async def monitor_questions():
        import asyncio
        try:
            while True:
                # Wait for event
                question = await InteractionManager.wait_for_question(project_id)
                if question:
                    await stream_output("ask_human", question)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Question monitor error: {e}")
            await asyncio.sleep(1)

    question_task = asyncio.create_task(monitor_questions())

    try:
        # Log callback — scoped to this project's WS connection
        async def log_callback(msg_type: str, content: str):
            await stream_output(msg_type, content)

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "user_message":
                user_content = message["content"]

                # Save user message to DB
                await stream_output("user_message", user_content)

                # Cancel any currently running task for this project
                old_task = _active_tasks.pop(project_id, None)
                if old_task and not old_task.done():
                    old_task.cancel()
                    try:
                        await asyncio.wait_for(asyncio.shield(old_task), timeout=2.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass

                # Set project context for AskHuman
                from app.context import project_id_var
                token = project_id_var.set(project_id)

                # Detect resume before deciding whether to create a fresh flow
                _trimmed = user_content.strip().lower()
                _existing_flow = _project_flows.get(project_id)
                _is_resume = (
                    _existing_flow is not None
                    and _existing_flow.can_resume
                    and any(kw in _trimmed for kw in RESUME_KEYWORDS)
                )

                if _is_resume:
                    flow = _existing_flow
                else:
                    # Fresh agents + fresh flow for each new execution
                    planning_agent = create_planning_agent()
                    executor_agent = create_math_modeling_agent()
                    flow = PlanningFlow(
                        planning_agent,
                        executor_agent,
                        on_log=log_callback,
                    )
                    _project_flows[project_id] = flow

                async def _run_flow(flow=flow, user_content=user_content, token=token, _is_resume=_is_resume):
                    try:
                        async def phase_gate(phase_name: str):
                            """Wait for user to confirm before proceeding to next phase."""
                            event = asyncio.Event()
                            _phase_confirm_events[project_id] = event
                            await event.wait()

                        if _is_resume:
                            await stream_output("status", "Resuming from checkpoint...")
                            result = await flow.resume()
                        else:
                            # Clear stale sandbox namespace for this project
                            from app.tool.python_execute import reset_namespace
                            reset_namespace(project_id)
                            await stream_output("status", "Agent starting...")
                            result = await flow.execute(user_content, phase_gate=phase_gate)
                        await stream_output("assistant_message", result)
                    except asyncio.CancelledError:
                        logger.info(f"Flow cancelled for project {project_id}")
                        await stream_output("status", "stopped")
                        await stream_output("assistant_message", "⏹️ 已停止当前对话。")
                    except Exception as e:
                        logger.error(f"Flow execution error: {e}")
                        await stream_output("error", str(e))
                    finally:
                        project_id_var.reset(token)
                        _active_tasks.pop(project_id, None)
                        _drop_finished_flow(project_id)

                # Run as a cancellable task
                task = asyncio.create_task(_run_flow())
                _active_tasks[project_id] = task
                # Don't await — we listen for more messages while it runs

            elif message["type"] == "stop":
                # Cancel the running flow task
                task = _active_tasks.pop(project_id, None)
                if task and not task.done():
                    task.cancel()
                    logger.info(f"User requested stop for project {project_id}")
                else:
                    await stream_output("status", "idle")

            elif message["type"] == "human_response":
                # Handle response to AskHuman
                response_content = message.get("content", "")
                InteractionManager.submit_response(project_id, response_content)
                await stream_output("status", "Received human response.")

            elif message["type"] == "phase_confirm":
                # User confirmed to proceed to next phase
                _phase_confirm_data.pop(project_id, None)
                event = _phase_confirm_events.pop(project_id, None)
                if event:
                    event.set()
                # Clear phase_confirm from DB so it won't re-appear on reload
                try:
                    from app.models.database import async_session
                    from app.models.project import Project
                    from sqlalchemy import select
                    async with async_session() as session:
                        result = await session.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
                        proj = result.scalars().first()
                        if proj and proj.shared_context:
                            ctx = dict(proj.shared_context)
                            ctx.pop("phase_confirm", None)
                            proj.shared_context = ctx
                            await session.commit()
                except Exception as e:
                    logger.error(f"Failed to clear phase_confirm: {e}")
                finally:
                    _drop_finished_flow(project_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
        question_task.cancel()
        _drop_finished_flow(project_id)
    except Exception as e:
        logger.error(f"WS endpoint error: {e}")
        manager.disconnect(websocket, project_id)
        question_task.cancel()
        _drop_finished_flow(project_id)
