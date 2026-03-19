"""Memory package — two-tier memory system for MathModelingAgent.

Architecture (inspired by memU):

  Tier 1 — Short-term memory (ShortTermMemory)
    Bounded, session-scoped working memory.
    Cleared at phase boundaries.  Holds recent step results for the
    immediate context window.

  Tier 2 — Long-term memory (LongTermMemory)
    Persistent, importance-scored knowledge store.
    Phase syntheses (importance=2.0) survive session restarts and are
    used to build cross-phase context for planning.

  MemoryManager
    Unified orchestrator.  PlanningFlow interacts exclusively with
    MemoryManager, which delegates to the appropriate tier.

Usage:
    from app.memory import MemoryManager

    memory = MemoryManager(executor_agent, project_id, session_id)
    await memory.start_phase("inception")
    await memory.record_step("inception", 0, "分析题目", result)
    ctx = await memory.build_step_context("inception", 1)
    synthesis = await memory.synthesize_phase("inception", on_log=log)
"""

from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.manager import MemoryManager

__all__ = ["ShortTermMemory", "LongTermMemory", "MemoryManager"]
