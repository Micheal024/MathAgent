"""Interaction Manager for cross-thread Agent-User communication.

Bridges the synchronous Agent execution (running in a thread)
with the asynchronous WebSocket handler (running on the main loop).
"""

import asyncio
from typing import Dict, Optional, Tuple
from concurrent.futures import Future as ThreadFuture, TimeoutError as FutureTimeoutError

# How long the agent tool will wait for a human response before giving up
_HUMAN_RESPONSE_TIMEOUT = 300  # seconds


class InteractionManager:
    """Manages synchronous interactions between Agent and WebSocket."""

    # key: project_id, value: (question, future_to_resolve_in_thread)
    _pending_requests: Dict[str, Tuple[str, ThreadFuture]] = {}
    _loop: Optional[asyncio.AbstractEventLoop] = None

    # Events are always created on the main loop via call_soon_threadsafe
    _events: Dict[str, asyncio.Event] = {}

    @classmethod
    def set_loop(cls, loop: asyncio.AbstractEventLoop):
        cls._loop = loop

    @classmethod
    async def wait_for_question(cls, project_id: str) -> str:
        """Called by WS HANDLER to wait for a question."""
        if project_id not in cls._events:
            cls._events[project_id] = asyncio.Event()
        await cls._events[project_id].wait()
        cls._events[project_id].clear()
        return cls.get_pending_question(project_id) or ""

    @classmethod
    def request_input_sync(cls, project_id: str, question: str) -> str:
        """Called by TOOL (sync, in thread). Blocks until response or timeout."""
        future: ThreadFuture = ThreadFuture()
        cls._pending_requests[project_id] = (question, future)

        if cls._loop:
            def _trigger():
                if project_id not in cls._events:
                    cls._events[project_id] = asyncio.Event()
                cls._events[project_id].set()

            cls._loop.call_soon_threadsafe(_trigger)

        try:
            return future.result(timeout=_HUMAN_RESPONSE_TIMEOUT)
        except FutureTimeoutError:
            cls._pending_requests.pop(project_id, None)
            return "[timeout] 用户未在规定时间内回复，跳过此步骤。"

    @classmethod
    def submit_response(cls, project_id: str, response: str) -> bool:
        """Called by WS HANDLER (async, main loop)."""
        if project_id in cls._pending_requests:
            _, future = cls._pending_requests[project_id]
            if not future.done():
                future.set_result(response)
            del cls._pending_requests[project_id]
            return True
        return False

    @classmethod
    def get_pending_question(cls, project_id: str) -> Optional[str]:
        if project_id in cls._pending_requests:
            return cls._pending_requests[project_id][0]
        return None
