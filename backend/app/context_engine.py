"""ContextEngine — Context building and LLM-driven phase synthesis.

Bridges the ContextStore (persistence layer) with the LLM agent (synthesis layer).

Core responsibilities:
  1. store_step_result   — persist completed step output as a MemoryItem
  2. build_step_context  — assemble a structured context window for the next step
  3. build_planning_context — assemble cross-phase context for plan decomposition
  4. synthesize_phase    — call the LLM to convert discrete step outputs into
                           a single coherent prose document per phase

Design principles (inspired by memU dual-retrieval):
  - Structural retrieval: phase membership and step ordering
  - Keyword retrieval:    extracted keywords stored on MemoryItem
  - LLM synthesis:        transforms "step dump" into publication-quality text
  - Clean agent state:    executor_agent is reset before/after synthesis so its
                          internal conversation history is never contaminated
"""

from __future__ import annotations

import asyncio
from typing import Callable, List, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from loguru import logger

from app.context_store import ContextStore
from app.models.project import MemoryItem


# ---------------------------------------------------------------------------
# Per-phase synthesis prompts
# ---------------------------------------------------------------------------

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

# Minimum total content length to warrant an LLM synthesis call.
# Below this threshold the step results are returned as-is.
_MIN_SYNTHESIS_CHARS = 300

# Maximum step-results text fed into the synthesis prompt.
# Keeps the synthesis request within typical context windows.
_MAX_STEP_RESULTS_CHARS = 8000


class ContextEngine:
    """Orchestrates context engineering across the planning flow.

    Parameters
    ----------
    executor_agent:
        The Camel AI ``ChatAgent`` used for step execution.  The same agent
        is reused for synthesis (with a reset before and after) to avoid
        spinning up a second LLM connection.
    """

    def __init__(self, executor_agent: ChatAgent) -> None:
        self._store = ContextStore()
        self._agent = executor_agent

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def store_step_result(
        self,
        project_id: str,
        phase: str,
        step_index: int,
        step_title: str,
        content: str,
    ) -> MemoryItem:
        """Persist a completed step's output as a structured MemoryItem."""
        return await self._store.add_item(
            project_id=project_id,
            phase=phase,
            step_index=step_index,
            step_title=step_title,
            content=content,
            content_type="result",
        )

    async def build_step_context(
        self,
        project_id: str,
        phase: str,
        step_index: int,
        max_chars: int = 3000,
    ) -> str:
        """Return a structured context window for an about-to-run step.

        Includes (in priority order):
          1. Synthesis summaries from all previously completed phases
          2. Results from earlier steps in the current phase (recency-first)
        """
        return await self._store.build_context_window(
            project_id=project_id,
            current_phase=phase,
            current_step_index=step_index,
            max_chars=max_chars,
        )

    async def build_planning_context(
        self,
        project_id: str,
        phase: str,
        fallback_context: str = "",
        max_chars: int = 2000,
    ) -> str:
        """Return context suitable for plan decomposition.

        Uses synthesis items from completed phases; falls back to
        ``fallback_context`` (the old raw-string accumulation) when no
        structured data is available yet.
        """
        structured = await self._store.build_cross_phase_context(
            project_id=project_id,
            current_phase=phase,
            max_chars=max_chars,
        )
        return structured if structured else fallback_context

    async def synthesize_phase(
        self,
        project_id: str,
        phase: str,
        on_log: Optional[Callable] = None,
    ) -> str:
        """Synthesize all step results for a phase into a coherent document.

        Algorithm:
          1. Load all non-synthesis MemoryItems for this phase.
          2. Concatenate them into a single ``step_results`` block.
          3. If the total is too short, return the concatenation unchanged.
          4. Otherwise, build the phase-specific synthesis prompt and call
             the LLM (executor_agent) with a clean, reset context.
          5. Persist the synthesized text as a ``synthesis`` MemoryItem so
             that subsequent phases can retrieve it cheaply.
          6. Reset the agent again so the planning flow is unaffected.

        Returns
        -------
        str
            The synthesized (or raw-concatenated) phase output.
        """
        items = await self._store.get_phase_items(project_id, phase)

        if not items:
            return f"## {phase.title()} 阶段\n（无执行结果）"

        # Build step results block
        parts: list[str] = []
        for item in items:
            parts.append(
                f"**步骤 {item.step_index + 1}：{item.step_title}**\n{item.content}"
            )
        step_results_text = "\n\n---\n\n".join(parts)

        # Skip LLM if content is trivially short
        if len(step_results_text) < _MIN_SYNTHESIS_CHARS:
            await self._persist_synthesis(project_id, phase, step_results_text)
            return step_results_text

        if on_log:
            msg = f"🔄 正在综合 {phase} 阶段内容（共 {len(items)} 步）..."
            try:
                if asyncio.iscoroutinefunction(on_log):
                    await on_log("thought", msg)
            except Exception:
                pass

        prompt_template = _SYNTHESIS_PROMPTS.get(
            phase,
            "请综合以下步骤结果，生成连贯的报告：\n\n{step_results}",
        )
        prompt_text = prompt_template.format(
            step_results=step_results_text[:_MAX_STEP_RESULTS_CHARS]
        )

        synthesized = await self._call_llm_for_synthesis(prompt_text, step_results_text)

        if on_log:
            msg = f"✅ {phase} 阶段综合完成（{len(synthesized)} 字）"
            try:
                if asyncio.iscoroutinefunction(on_log):
                    await on_log("thought", msg)
            except Exception:
                pass

        await self._persist_synthesis(project_id, phase, synthesized)
        return synthesized

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_llm_for_synthesis(
        self, prompt_text: str, fallback: str
    ) -> str:
        """Call the executor agent for synthesis with a clean slate.

        The agent is reset before the call and reset again afterwards so
        that its internal conversation history is not polluted.
        """
        self._agent.reset()
        try:
            loop = asyncio.get_running_loop()
            msg = BaseMessage.make_user_message(
                role_name="User", content=prompt_text
            )
            response = await loop.run_in_executor(
                None, lambda: self._agent.step(msg)
            )
            result = response.msgs[0].content if response.msgs else fallback
        except Exception as exc:
            logger.warning(f"ContextEngine: synthesis LLM call failed — {exc}")
            result = fallback
        finally:
            self._agent.reset()
        return result

    async def _persist_synthesis(
        self, project_id: str, phase: str, content: str
    ) -> None:
        """Store a synthesis result as a special MemoryItem (step_index=9999)."""
        try:
            await self._store.add_item(
                project_id=project_id,
                phase=phase,
                step_index=9999,
                step_title=f"{phase.title()} 阶段综合",
                content=content,
                content_type="synthesis",
            )
        except Exception as exc:
            logger.warning(f"ContextEngine: failed to persist synthesis for {phase} — {exc}")
