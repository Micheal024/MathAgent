"""MemoryManager — orchestrates short-term and long-term memory.

Single entry point for all memory operations inside PlanningFlow.

Two-tier design (inspired by memU):

  Short-term (ShortTermMemory)
    - Session-scoped, ephemeral, bounded (≤6000 chars/phase)
    - Cleared at phase boundaries to free capacity
    - Provides "what happened recently" for the next step

  Long-term (LongTermMemory)
    - Project-scoped, persistent, importance-scored
    - Phase syntheses survive across restarts
    - Provides "what was learned before" for planning and cross-phase context

Context window assembly for a step:
  ┌─────────────────────────────────────────────────────┐
  │ Long-term: previous phase syntheses (≤60% budget)   │
  │ Short-term: recent steps in current phase           │
  └─────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
from typing import Callable, List, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from loguru import logger

from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory

# Per-phase LLM synthesis prompts
_SYNTHESIS_PROMPTS: dict[str, str] = {
    "inception": (
        "你是一位资深数学建模专家。以下是\u300c破题与分析\u300d阶段各步骤的执行结果，"
        "请综合整理，生成一份完整、连贯的**问题分析报告**。\n\n"
        "报告要求：\n"
        "- 使用 Markdown 格式\n"
        "- 包含：背景概述、关键变量识别、约束条件分析、问题类型判断、文献调研结论\n"
        "- 语言流畅，逻辑清晰；综合提炼，而非简单罗列步骤\n"
        "- 篇幅：800-2000 字\n\n"
        "各步骤结果如下：\n\n{step_results}\n\n"
        "请生成综合问题分析报告："
    ),
    "blueprinting": (
        "你是一位资深数学建模专家。以下是\u300c建模方案设计\u300d阶段各步骤的执行结果，"
        "请综合整理，生成一份完整的**建模方案蓝图**。\n\n"
        "蓝图要求：\n"
        "- 使用 Markdown + LaTeX 数学公式格式\n"
        "- 包含：模型总体设计、数学模型描述（含公式）、算法选择与说明、数据需求、求解流程\n"
        "- 综合各步骤洞察，形成统一建模方案，而非简单拼接\n"
        "- 篇幅：1000-3000 字\n\n"
        "各步骤结果如下：\n\n{step_results}\n\n"
        "请生成建模方案蓝图："
    ),
    "coding": (
        "你是一位资深数学建模专家。以下是\u300c代码实现与求解\u300d阶段各步骤的执行结果，"
        "请综合整理，生成一份完整的**求解结果报告**。\n\n"
        "报告要求：\n"
        "- 使用 Markdown 格式\n"
        "- 包含：实现方案概述、关键代码逻辑说明、求解结果分析、图表说明、模型验证\n"
        "- 重点阐述求解结论与数值结果，不要逐行复制代码\n"
        "- 篇幅：800-2000 字\n\n"
        "各步骤结果如下：\n\n{step_results}\n\n"
        "请生成求解结果报告："
    ),
    "writing": (
        "你是一位资深数学建模专家。以下是\u300c论文撰写\u300d阶段各步骤的执行结果，"
        "请综合整理，描述论文最终状态及撰写过程摘要。\n\n"
        "要求：\n"
        "- 包含：论文结构说明、各章节核心内容摘要、合规性检查结果\n"
        "- 简洁清晰，说明最终产出物\n\n"
        "各步骤结果如下：\n\n{step_results}\n\n"
        "请生成论文撰写总结："
    ),
}

_MIN_SYNTHESIS_CHARS = 300
_MAX_STEP_RESULTS_FOR_SYNTHESIS = 8000


class MemoryManager:
    """Unified memory interface for PlanningFlow.

    Parameters
    ----------
    executor_agent:
        The Camel AI ChatAgent used for step execution.
    project_id:
        UUID string of the current project.
    session_id:
        UUID string identifying the current WebSocket / agent run.
    synthesis_agent:
        Optional lightweight ChatAgent (no tools) used exclusively for
        LLM synthesis calls.  When provided it is preferred over
        executor_agent for synthesis so that tool-schema overhead does
        not inflate the context window and trigger provider errors.
        Pass the planning_agent here.
    """

    def __init__(
        self,
        executor_agent: ChatAgent,
        project_id: str,
        session_id: str,
        synthesis_agent: Optional[ChatAgent] = None,
    ) -> None:
        self._agent = executor_agent
        self._synthesis_agent = synthesis_agent if synthesis_agent is not None else executor_agent
        self._project_id = project_id
        self._session_id = session_id
        self.short_term = ShortTermMemory(project_id, session_id)
        self.long_term = LongTermMemory()

    # ------------------------------------------------------------------
    # Phase lifecycle
    # ------------------------------------------------------------------

    async def start_phase(self, phase: str) -> None:
        """Clear short-term memory at the beginning of a new phase.

        This frees capacity and ensures the short-term window only contains
        entries relevant to the current phase.
        """
        await self.short_term.clear_phase(phase)

    # ------------------------------------------------------------------
    # Recording results
    # ------------------------------------------------------------------

    async def record_step(
        self,
        phase: str,
        step_index: int,
        step_title: str,
        content: str,
    ) -> None:
        """Store a completed step result in both memory tiers.

        Short-term: provides immediate context for the next step.
        Long-term: persists for cross-phase retrieval and future sessions.
        """
        short_content = f"步骤 {step_index + 1} [{step_title}]:\n{content}"

        await asyncio.gather(
            self.short_term.add(
                content=short_content,
                phase=phase,
                content_type="step_result",
                role="agent",
            ),
            self.long_term.remember_step(
                project_id=self._project_id,
                phase=phase,
                step_index=step_index,
                step_title=step_title,
                content=content,
                content_type="result",
            ),
        )

    async def record_user_decision(
        self,
        phase: str,
        question: str,
        answer: str,
    ) -> None:
        """Store a user decision (from ask_human) in long-term memory.

        User decisions are high-importance (1.8) because they represent
        explicit intent that must be honoured across phases.
        """
        content = f"问：{question}\n答：{answer}"
        await self.long_term.remember(
            project_id=self._project_id,
            title=f"用户决策 — {question[:60]}",
            content=content,
            phase=phase,
            content_type="user_decision",
            importance=1.8,
        )

    # ------------------------------------------------------------------
    # Context window construction
    # ------------------------------------------------------------------

    async def build_step_context(
        self,
        phase: str,
        step_index: int,
        max_chars: int = 4000,
    ) -> str:
        """Assemble a combined context window for a step.

        Layout (fills budget greedily in priority order):

          1. Long-term: previous phase syntheses     (~40% budget)
          2. Short-term: recent steps in this phase  (~60% budget)

        The split is soft — if short-term is sparse, long-term gets more.
        """
        lt_budget = int(max_chars * 0.45)
        st_budget = max_chars - lt_budget

        lt_context = await self.long_term.build_step_context(
            project_id=self._project_id,
            current_phase=phase,
            current_step_index=step_index,
            max_chars=lt_budget,
        )
        st_context = await self.short_term.get_window(
            phase=phase,
            max_chars=st_budget,
        )

        parts = []
        if lt_context:
            parts.append("## 长期记忆（跨阶段知识）\n" + lt_context)
        if st_context:
            parts.append("## 短期记忆（当前阶段步骤）\n" + st_context)

        return "\n\n".join(parts)

    async def build_planning_context(
        self,
        phase: str,
        fallback: str = "",
        max_chars: int = 2000,
    ) -> str:
        """Build context for plan decomposition.

        Uses only long-term (synthesis) items so the planner sees a
        compact, high-quality summary of completed phases.
        Falls back to ``fallback`` (raw accumulated string) when empty.
        """
        structured = await self.long_term.build_phase_context(
            project_id=self._project_id,
            current_phase=phase,
            max_chars=max_chars,
        )
        return structured if structured else fallback

    # ------------------------------------------------------------------
    # Phase synthesis
    # ------------------------------------------------------------------

    async def synthesize_phase(
        self,
        phase: str,
        on_log: Optional[Callable] = None,
    ) -> str:
        """Synthesize all step results for a phase into coherent prose.

        Algorithm:
          1. Load all non-synthesis MemoryItems for the phase.
          2. Skip synthesis if content is too sparse.
          3. Build the phase-specific synthesis prompt.
          4. Call the LLM (executor_agent reset before + after).
          5. Store synthesis in long-term memory (importance=2.0).
          6. Return the synthesized text.
        """
        items = await self.long_term.recall_by_phase(self._project_id, phase)

        if not items:
            return f"## {phase.title()} 阶段\n（无执行结果）"

        parts: list[str] = []
        for item in items:
            parts.append(
                f"**步骤 {item.step_index + 1}：{item.step_title}**\n{item.content}"
            )
        step_results_text = "\n\n---\n\n".join(parts)

        # Too short — return raw concatenation
        if len(step_results_text) < _MIN_SYNTHESIS_CHARS:
            await self._store_synthesis(phase, step_results_text)
            return step_results_text

        if on_log:
            msg = f"🔄 正在综合 {phase} 阶段内容（共 {len(items)} 步）..."
            try:
                if asyncio.iscoroutinefunction(on_log):
                    await on_log("thought", msg)
            except Exception:
                pass

        prompt_template = _SYNTHESIS_PROMPTS.get(
            phase, "请综合以下步骤结果，生成连贯的报告：\n\n{step_results}"
        )
        prompt_text = prompt_template.format(
            step_results=step_results_text[:_MAX_STEP_RESULTS_FOR_SYNTHESIS]
        )

        synthesized = await self._llm_synthesize(prompt_text, step_results_text)

        if on_log:
            msg = f"✅ {phase} 阶段综合完成（{len(synthesized)} 字）"
            try:
                if asyncio.iscoroutinefunction(on_log):
                    await on_log("thought", msg)
            except Exception:
                pass

        await self._store_synthesis(phase, synthesized)
        return synthesized

    # ------------------------------------------------------------------
    # Frontend state snapshot
    # ------------------------------------------------------------------

    async def get_memory_state(self) -> dict:
        """Return a serialisable memory state for the memory_update WS event.

        Format expected by the frontend renderMemoryDrawer():
            {
              "working":  {"vars": [...], "usage": 0-100},
              "session":  {"items": [...], "usage": 0-100},
              "project":  {"items": [...], "usage": 0-100},
              "longterm": {"items": [...], "count": int, "usage": 0-100},
            }
        """
        try:
            from sqlalchemy import select, func as sa_func
            from app.models.database import async_session
            from app.models.project import ShortTermMemoryEntry, MemoryItem
            import uuid as _uuid

            pid = _uuid.UUID(str(self._project_id))

            async with async_session() as session:
                # --- Working memory: recent short-term entries (last 5) ---
                st_result = await session.execute(
                    select(ShortTermMemoryEntry)
                    .where(ShortTermMemoryEntry.project_id == pid,
                           ShortTermMemoryEntry.session_id == self._session_id)
                    .order_by(ShortTermMemoryEntry.sequence_num.desc())
                    .limit(5)
                )
                st_entries = list(st_result.scalars().all())
                working_vars = [e.content[:60] for e in reversed(st_entries)]

                # --- Session memory: all short-term items, last 8, grouped by phase ---
                sess_result = await session.execute(
                    select(ShortTermMemoryEntry)
                    .where(ShortTermMemoryEntry.project_id == pid,
                           ShortTermMemoryEntry.session_id == self._session_id)
                    .order_by(ShortTermMemoryEntry.sequence_num.desc())
                    .limit(8)
                )
                sess_entries = list(sess_result.scalars().all())
                session_items = [f"[{e.phase}] {e.content[:50]}" for e in reversed(sess_entries)]

                # --- Project memory: high-importance long-term items ---
                lt_result = await session.execute(
                    select(MemoryItem)
                    .where(MemoryItem.project_id == pid,
                           MemoryItem.importance >= 1.5)
                    .order_by(MemoryItem.importance.desc(), MemoryItem.created_at.desc())
                    .limit(6)
                )
                lt_items = list(lt_result.scalars().all())
                project_items = [f"[{i.phase}] {i.step_title[:50]}" for i in lt_items]

                # --- Long-term: synthesis count ---
                count_result = await session.execute(
                    select(sa_func.count(MemoryItem.id))
                    .where(MemoryItem.project_id == pid,
                           MemoryItem.content_type == "synthesis")
                )
                lt_count = count_result.scalar_one_or_none() or 0

                lt_titles_result = await session.execute(
                    select(MemoryItem.step_title)
                    .where(MemoryItem.project_id == pid,
                           MemoryItem.content_type == "synthesis")
                    .order_by(MemoryItem.created_at.desc())
                    .limit(4)
                )
                lt_titles = [row[0] for row in lt_titles_result.all()]

            return {
                "working": {
                    "vars": working_vars,
                    "usage": min(100, len(working_vars) * 20),
                },
                "session": {
                    "items": session_items,
                    "usage": min(100, len(session_items) * 12),
                },
                "project": {
                    "items": project_items,
                    "usage": min(100, len(project_items) * 15),
                },
                "longterm": {
                    "items": lt_titles,
                    "count": lt_count,
                    "usage": min(100, lt_count * 8),
                },
            }
        except Exception as exc:
            logger.debug(f"MemoryManager.get_memory_state failed: {exc}")
            return {
                "working":  {"vars": [], "usage": 0},
                "session":  {"items": [], "usage": 0},
                "project":  {"items": [], "usage": 0},
                "longterm": {"items": [], "count": 0, "usage": 0},
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _llm_synthesize(self, prompt_text: str, fallback: str) -> str:
        """Call the synthesis agent (no tools) with a clean slate."""
        self._synthesis_agent.reset()
        try:
            loop = asyncio.get_running_loop()
            msg = BaseMessage.make_user_message(
                role_name="User", content=prompt_text
            )
            response = await loop.run_in_executor(
                None, lambda: self._synthesis_agent.step(msg)
            )
            result = response.msgs[0].content if response.msgs else fallback
        except Exception as exc:
            logger.warning(f"MemoryManager: synthesis LLM call failed — {exc}")
            result = fallback
        finally:
            self._synthesis_agent.reset()
        return result

    async def _store_synthesis(self, phase: str, content: str) -> None:
        """Persist synthesis in long-term memory (importance=2.0)."""
        try:
            await self.long_term.remember(
                project_id=self._project_id,
                title=f"{phase.title()} 阶段综合",
                content=content,
                phase=phase,
                content_type="synthesis",
                importance=2.0,
            )
        except Exception as exc:
            logger.warning(f"MemoryManager: failed to persist synthesis — {exc}")
