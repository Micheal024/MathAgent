"""ContextStore — Structured memory persistence and retrieval.

Implements the storage and retrieval layer for the context engineering system,
inspired by the memU memory framework's three-layer architecture:

  Layer 1: Project (Resource) — existing model
  Layer 2: Phase (MemoryCategory) — inception / blueprinting / coding / writing
  Layer 3: MemoryItem — individual step results with metadata

Retrieval strategies (no external vector DB required):
  - Structural: by phase and step_index
  - Keyword-based: simple Chinese/English keyword matching
  - Recency: most recent items are prioritized within budget
"""

from __future__ import annotations

import re
import uuid
from typing import List, Optional

from sqlalchemy import select

from app.models.database import async_session
from app.models.project import MemoryItem

# Phase execution order — used for cross-phase context building
PHASE_ORDER = ["inception", "blueprinting", "coding", "writing"]


class ContextStore:
    """Manages structured memory items for a single project.

    Each completed step is persisted as a MemoryItem with:
    - Phase membership (which phase produced it)
    - Step metadata (title, index) for ordering and display
    - Full content for synthesis
    - Extracted keywords for lightweight retrieval

    A special ``content_type="synthesis"`` item is stored after each phase,
    containing the LLM-generated coherent summary of all step results.
    """

    async def add_item(
        self,
        project_id: str,
        phase: str,
        step_index: int,
        step_title: str,
        content: str,
        content_type: str = "result",
    ) -> MemoryItem:
        """Persist a step result as a MemoryItem."""
        keywords = self._extract_keywords(content)
        async with async_session() as session:
            item = MemoryItem(
                project_id=uuid.UUID(str(project_id)),
                phase=phase,
                step_index=step_index,
                step_title=step_title,
                content=content,
                content_type=content_type,
                keywords=keywords,
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item

    async def get_phase_items(
        self, project_id: str, phase: str
    ) -> List[MemoryItem]:
        """Return all non-synthesis MemoryItems for a phase, ordered by step_index."""
        async with async_session() as session:
            result = await session.execute(
                select(MemoryItem)
                .where(
                    MemoryItem.project_id == uuid.UUID(str(project_id)),
                    MemoryItem.phase == phase,
                    MemoryItem.content_type != "synthesis",
                )
                .order_by(MemoryItem.step_index, MemoryItem.created_at)
            )
            return list(result.scalars().all())

    async def get_phase_synthesis(
        self, project_id: str, phase: str
    ) -> Optional[MemoryItem]:
        """Return the latest synthesis item for a phase, or None."""
        async with async_session() as session:
            result = await session.execute(
                select(MemoryItem)
                .where(
                    MemoryItem.project_id == uuid.UUID(str(project_id)),
                    MemoryItem.phase == phase,
                    MemoryItem.content_type == "synthesis",
                )
                .order_by(MemoryItem.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def build_context_window(
        self,
        project_id: str,
        current_phase: str,
        current_step_index: int,
        max_chars: int = 3000,
    ) -> str:
        """Build a smart context window for an in-progress step.

        Priority order (fills budget greedily):
          1. Synthesis summaries from all completed previous phases
             — compact, high-value cross-phase context
          2. Results from earlier steps in the current phase
             — most recent items first (recency weighting)

        Returns an empty string if no relevant items exist yet.
        """
        parts: list[str] = []
        used_chars = 0
        budget = max_chars

        # --- 1. Previous phase syntheses ---
        current_idx = PHASE_ORDER.index(current_phase) if current_phase in PHASE_ORDER else 0
        for prev_phase in PHASE_ORDER[:current_idx]:
            synthesis = await self.get_phase_synthesis(project_id, prev_phase)
            if synthesis:
                # Allow syntheses to use up to 60 % of the budget
                cap = int(budget * 0.6)
                snippet = synthesis.content[:cap]
                label = f"### 【{prev_phase.title()} 阶段综合】\n{snippet}"
                if used_chars + len(label) < budget:
                    parts.append(label)
                    used_chars += len(label)

        # --- 2. Earlier steps in current phase (recency-first) ---
        current_items = await self.get_phase_items(project_id, current_phase)
        prior_items = [i for i in current_items if i.step_index < current_step_index]
        for item in reversed(prior_items):
            # Truncate individual step snippets so one step cannot consume the budget
            snippet = item.content[:600] if len(item.content) > 600 else item.content
            entry = f"**步骤 {item.step_index + 1}：{item.step_title}**\n{snippet}"
            if used_chars + len(entry) < budget:
                parts.append(entry)
                used_chars += len(entry)
            else:
                break

        return "\n\n".join(parts)

    async def build_cross_phase_context(
        self,
        project_id: str,
        current_phase: str,
        max_chars: int = 2000,
    ) -> str:
        """Build context from completed previous phases for plan creation.

        Prefers synthesis items; falls back to the last step result of a phase
        when no synthesis exists yet.
        """
        current_idx = PHASE_ORDER.index(current_phase) if current_phase in PHASE_ORDER else 0
        parts: list[str] = []
        used_chars = 0

        for prev_phase in PHASE_ORDER[:current_idx]:
            synthesis = await self.get_phase_synthesis(project_id, prev_phase)
            if synthesis:
                snippet = synthesis.content[:800] if len(synthesis.content) > 800 else synthesis.content
                entry = f"### {prev_phase.title()} 阶段\n{snippet}"
            else:
                # Fallback: last step result of this phase
                items = await self.get_phase_items(project_id, prev_phase)
                if not items:
                    continue
                last = items[-1]
                snippet = last.content[:400] if len(last.content) > 400 else last.content
                entry = f"### {prev_phase.title()} 阶段（最后步骤）\n{snippet}"

            if used_chars + len(entry) < max_chars:
                parts.append(entry)
                used_chars += len(entry)

        return "\n\n".join(parts)

    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
        """Extract domain-relevant keywords from Chinese/English text.

        Steps:
          1. Strip code fences (low keyword density, high noise)
          2. Prioritise math-modeling domain terms
          3. Collect Chinese word candidates (2–6 character sequences)
          4. Collect English word candidates (4+ alphabetic chars)
          5. Deduplicate while preserving priority order
        """
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)

        # Domain-specific math modeling keywords (boosted priority)
        domain_kws = re.findall(
            r"(?:优化|模型|算法|预测|评价|分析|结果|数据|方程|矩阵|"
            r"回归|分类|聚类|神经网络|遗传|退火|规划|约束|目标函数|"
            r"灵敏度|验证|仿真|数值|参数|变量|假设|结论|图表|代码)",
            text,
        )

        # Chinese character n-grams (2–6 chars)
        chinese_words = re.findall(r"[\u4e00-\u9fff]{2,6}", text)

        # English words (4+ chars, lowercased)
        english_words = re.findall(r"[a-zA-Z]{4,}", text.lower())

        all_candidates = domain_kws + chinese_words[:12] + english_words[:8]

        seen: set[str] = set()
        unique: list[str] = []
        for kw in all_candidates:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
                if len(unique) >= max_keywords:
                    break
        return unique
