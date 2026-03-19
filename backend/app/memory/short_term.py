"""Short-term memory — bounded, session-scoped working memory.

Short-term memory holds the most recent step results, tool outputs, and
thoughts from the *current* execution session.  It acts as the agent's
"working scratchpad":

  - Bounded: maximum MAX_CHARS characters per phase-slot
  - Session-scoped: each WebSocket connection gets a fresh session_id
  - Phase-aware: can be cleared at phase boundaries to free capacity
  - Fast: full content stored in DB; window built by simple SELECT + join

Retrieval returns entries in reverse-chronological order so the most
recent steps fill the context window first (recency weighting).
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select, func, delete

from app.models.database import async_session
from app.models.project import ShortTermMemoryEntry

# Maximum total chars allowed per (session_id, phase) slot.
# When exceeded, the oldest entries are deleted until under capacity.
MAX_CHARS_PER_PHASE = 6000

# How many characters one entry may use in a context window.
# Longer entries are truncated to keep the window balanced.
MAX_ENTRY_CHARS_IN_WINDOW = 600

# Phase execution order (used for cross-phase ordering)
PHASE_ORDER = ["inception", "blueprinting", "coding", "writing"]


class ShortTermMemory:
    """Bounded, session-scoped working memory.

    Parameters
    ----------
    project_id:
        The UUID of the project this memory belongs to.
    session_id:
        Unique identifier for the current agent run.  Set once per WS
        session so that entries from different runs don't mix.
    """

    def __init__(self, project_id: str, session_id: str) -> None:
        self.project_id = project_id
        self.session_id = session_id
        self._pid = uuid.UUID(str(project_id))

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def add(
        self,
        content: str,
        phase: str,
        content_type: str = "step_result",
        role: str = "agent",
    ) -> ShortTermMemoryEntry:
        """Append an entry, evicting oldest entries if over capacity.

        Steps:
        1. Compute the next sequence number.
        2. Insert the entry.
        3. Evict oldest entries for this phase until under MAX_CHARS.
        """
        char_count = len(content)

        async with async_session() as session:
            # Next sequence number
            result = await session.execute(
                select(func.max(ShortTermMemoryEntry.sequence_num))
                .where(
                    ShortTermMemoryEntry.project_id == self._pid,
                    ShortTermMemoryEntry.session_id == self.session_id,
                )
            )
            max_seq = result.scalar_one_or_none() or 0

            entry = ShortTermMemoryEntry(
                project_id=self._pid,
                session_id=self.session_id,
                sequence_num=max_seq + 1,
                phase=phase,
                role=role,
                content_type=content_type,
                content=content,
                char_count=char_count,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)

        # Evict oldest entries to stay within capacity
        await self._evict_if_over_capacity(phase)
        return entry

    async def clear_phase(self, phase: str) -> None:
        """Delete all entries for this session+phase.

        Called at the start of a new phase to free capacity.
        """
        async with async_session() as session:
            await session.execute(
                delete(ShortTermMemoryEntry).where(
                    ShortTermMemoryEntry.project_id == self._pid,
                    ShortTermMemoryEntry.session_id == self.session_id,
                    ShortTermMemoryEntry.phase == phase,
                )
            )
            await session.commit()

    async def clear_session(self) -> None:
        """Delete all entries for this session (e.g., on flow completion)."""
        async with async_session() as session:
            await session.execute(
                delete(ShortTermMemoryEntry).where(
                    ShortTermMemoryEntry.project_id == self._pid,
                    ShortTermMemoryEntry.session_id == self.session_id,
                )
            )
            await session.commit()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_window(
        self,
        phase: str,
        max_chars: int = 3000,
    ) -> str:
        """Build a formatted context window for the current phase.

        Returns entries in reverse-chronological order (most recent first)
        until the character budget is exhausted.
        """
        entries = await self._get_phase_entries(phase)
        if not entries:
            return ""

        parts: list[str] = []
        used = 0

        for entry in reversed(entries):  # most recent first
            snippet = (
                entry.content[:MAX_ENTRY_CHARS_IN_WINDOW]
                if len(entry.content) > MAX_ENTRY_CHARS_IN_WINDOW
                else entry.content
            )
            label = f"[{entry.content_type}] {snippet}"
            if used + len(label) > max_chars:
                break
            parts.append(label)
            used += len(label)

        # Reverse back so context reads oldest→newest
        return "\n\n".join(reversed(parts))

    async def get_phase_char_count(self, phase: str) -> int:
        """Total characters stored for a phase."""
        async with async_session() as session:
            result = await session.execute(
                select(func.sum(ShortTermMemoryEntry.char_count)).where(
                    ShortTermMemoryEntry.project_id == self._pid,
                    ShortTermMemoryEntry.session_id == self.session_id,
                    ShortTermMemoryEntry.phase == phase,
                )
            )
            return result.scalar_one_or_none() or 0

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _get_phase_entries(self, phase: str) -> List[ShortTermMemoryEntry]:
        async with async_session() as session:
            result = await session.execute(
                select(ShortTermMemoryEntry)
                .where(
                    ShortTermMemoryEntry.project_id == self._pid,
                    ShortTermMemoryEntry.session_id == self.session_id,
                    ShortTermMemoryEntry.phase == phase,
                )
                .order_by(ShortTermMemoryEntry.sequence_num)
            )
            return list(result.scalars().all())

    async def _evict_if_over_capacity(self, phase: str) -> None:
        """Delete oldest entries until total chars <= MAX_CHARS_PER_PHASE."""
        total = await self.get_phase_char_count(phase)
        if total <= MAX_CHARS_PER_PHASE:
            return

        entries = await self._get_phase_entries(phase)
        to_evict: list[uuid.UUID] = []
        for entry in entries:  # oldest first
            if total <= MAX_CHARS_PER_PHASE:
                break
            to_evict.append(entry.id)
            total -= entry.char_count

        if to_evict:
            async with async_session() as session:
                await session.execute(
                    delete(ShortTermMemoryEntry).where(
                        ShortTermMemoryEntry.id.in_(to_evict)
                    )
                )
                await session.commit()
