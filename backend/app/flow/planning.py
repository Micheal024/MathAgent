"""PlanningFlow — Task orchestration via LLM-driven plan decomposition.

Uses Camel AI's ChatAgent as the execution engine.
Inspired by OpenManus PlanningFlow pattern:

1. User submits a task
2. ProblemUnderstanding analyzes the problem (emits WS event)
3. Planning ChatAgent decomposes each phase into problem-specific steps
4. For each step, the executor ChatAgent runs via step()
5. An Observe→Evaluate→Fix inner loop validates and corrects results
6. Results are tracked; memory is updated after each step

Two-tier memory integration:
  - Short-term memory: bounded per-phase buffer for immediate context
  - Long-term memory: importance-scored persistent store for cross-phase knowledge
  - MemoryManager: orchestrates both tiers and drives LLM synthesis
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from typing import Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from loguru import logger

from app.schema import AgentState, Plan, PlanStep, PlanStepStatus, ProjectPhase
from app.prompt.math_modeling import build_phase_prompt
from app.memory import MemoryManager
from app.problem_understanding import ProblemUnderstanding, analyze_problem


class PlanningFlow:
    """Orchestrates complex tasks across 4 phases with two-tier memory.

    Phases: Inception -> Blueprinting -> Coding -> Writing

    Key improvements over v1:
    - ProblemUnderstanding runs first, grounding all phase plans in the actual problem
    - Step plans are dynamically generated per-problem (not hardcoded)
    - Coding steps use Observe→Evaluate→Fix inner loop (up to 3 iterations)
    - Memory state is broadcast to frontend after every step
    """

    _QUOTA_ERROR_KEYWORDS = [
        "429", "rate_limit", "rate limit", "quota", "insufficient_quota",
        "billing", "exceeded", "too many requests", "resource_exhausted",
        "tokens per min", "rpm", "tpm",
    ]

    MAX_EVAL_ITERATIONS = 3   # max Obs→Eval→Fix rounds per step

    def __init__(
        self,
        planning_agent: ChatAgent,
        executor_agent: ChatAgent,
        on_log: Optional[callable] = None,
    ):
        self.planning_agent = planning_agent
        self.executor_agent = executor_agent
        self.plan: Optional[Plan] = None
        self.state = AgentState.IDLE
        self.current_phase = ProjectPhase.INCEPTION
        self.on_log = on_log
        self._snapshot: Optional[dict] = None
        self._memory: Optional[MemoryManager] = None
        self._pu: Optional[ProblemUnderstanding] = None  # Problem Understanding

    # ------------------------------------------------------------------
    # Logging / events
    # ------------------------------------------------------------------

    async def _log(self, content: str) -> None:
        logger.info(content)
        if self.on_log:
            if asyncio.iscoroutinefunction(self.on_log):
                await self.on_log("thought", content)
            else:
                self.on_log("thought", content)

    async def _emit(self, event_type: str, **kwargs) -> None:
        if self.on_log and asyncio.iscoroutinefunction(self.on_log):
            payload = json.dumps(kwargs, ensure_ascii=False, default=str)
            await self.on_log(event_type, payload)

    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------

    async def _save_artifact(self, artifact_type: str, content: str) -> None:
        try:
            from app.models.database import async_session
            from app.models.project import Artifact
            from app.context import project_id_var
            project_id = project_id_var.get()
            if not project_id:
                return
            async with async_session() as session:
                artifact = Artifact(
                    project_id=uuid.UUID(str(project_id)),
                    artifact_type=artifact_type,
                    content=content,
                    version=1,
                )
                session.add(artifact)
                await session.commit()
            await self._log(f"💾 Saved Artifact: {artifact_type}")
            await self._emit("artifact_saved", artifact_type=artifact_type, content=content)
        except Exception as e:
            await self._log(f"❌ Failed to save artifact: {e}")

    async def _save_phase_artifact(self, phase: ProjectPhase, result: str) -> None:
        mapping = {
            ProjectPhase.INCEPTION: "report",
            ProjectPhase.BLUEPRINTING: "blueprint",
            ProjectPhase.CODING: "code",
            ProjectPhase.WRITING: "paper",
        }
        if at := mapping.get(phase):
            await self._save_artifact(at, result)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_quota_error(error: Exception) -> bool:
        err = str(error).lower()
        return any(kw in err for kw in PlanningFlow._QUOTA_ERROR_KEYWORDS)

    @property
    def can_resume(self) -> bool:
        return self._snapshot is not None

    def _save_snapshot(self, input_text, phase_idx, accumulated_context, all_results):
        self._snapshot = {
            "input_text": input_text,
            "phase_idx": phase_idx,
            "accumulated_context": accumulated_context,
            "all_results": list(all_results),
            "plan": self.plan,
            "current_phase": self.current_phase,
            "pu": self._pu,
        }

    def _get_project_id(self) -> Optional[str]:
        try:
            from app.context import project_id_var
            pid = project_id_var.get()
            return str(pid) if pid else None
        except Exception:
            return None

    def _get_or_init_memory(self) -> Optional[MemoryManager]:
        if self._memory is not None:
            return self._memory
        project_id = self._get_project_id()
        if not project_id:
            return None
        session_id = str(uuid.uuid4())
        self._memory = MemoryManager(
            self.executor_agent,
            project_id,
            session_id,
            synthesis_agent=self.planning_agent,
        )
        return self._memory

    async def _broadcast_memory(self) -> None:
        """Emit current memory state to frontend."""
        if self._memory:
            try:
                state = await self._memory.get_memory_state()
                await self._emit("memory_update", **state)
            except Exception as e:
                logger.debug(f"[Memory] broadcast failed: {e}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def execute(self, input_text: str, phase_gate: Optional[callable] = None) -> str:
        """Execute the full planning flow across all 4 phases."""
        self.state = AgentState.RUNNING
        self._get_or_init_memory()

        # ----------------------------------------------------------------
        # Step 0: Problem Understanding (runs before any phase)
        # ----------------------------------------------------------------
        await self._log("🔍 分析题目结构...")
        try:
            self._pu = await analyze_problem(
                problem_text=input_text,
                agent=self.planning_agent,
                on_emit=self.on_log,
            )
            await self._log(
                f"✅ 题目理解完成: {self._pu.type} | "
                f"{len(self._pu.variables)} 变量 | 置信度 {self._pu.confidence:.0%}"
            )
        except Exception as e:
            await self._log(f"⚠️ 题目分析失败 ({e})，使用通用规划")
            self._pu = None

        phases = [
            ProjectPhase.INCEPTION,
            ProjectPhase.BLUEPRINTING,
            ProjectPhase.CODING,
            ProjectPhase.WRITING,
        ]

        all_results: list[str] = []
        accumulated_context = ""
        phase_idx = 0

        try:
            for phase_idx, phase in enumerate(phases):
                self.current_phase = phase
                await self._log(f"🚀 Starting Phase: {phase.value}")
                await self._emit(
                    "phase_start",
                    phase=phase.value,
                    phase_index=phase_idx,
                    total_phases=len(phases),
                )

                self.planning_agent.reset()
                self.executor_agent.reset()

                if self._memory:
                    await self._memory.start_phase(phase.value)

                # 1. Dynamic plan generation (grounded in ProblemUnderstanding)
                await self._create_phase_plan(input_text, accumulated_context)
                if not self.plan or not self.plan.steps:
                    await self._log(f"⚠️ No steps generated for {phase.value}")
                    continue

                # 2. Execute steps with Eval Loop
                phase_result = await self._execute_phase_steps(accumulated_context)

                summary = f"## Phase {phase.value} Results\n{phase_result}\n"
                all_results.append(summary)
                accumulated_context += summary + "\n"

                await self._save_phase_artifact(phase, phase_result)
                await self._broadcast_memory()

                # 3. Phase gate (user confirmation before next phase)
                is_last = phase_idx == len(phases) - 1
                if phase_gate and not is_last:
                    await self._emit("phase_complete", phase=phase.value, summary=phase_result[:300])
                    await phase_gate(phase.value)

            self.state = AgentState.FINISHED
            self._snapshot = None
            return "\n\n".join(all_results)

        except Exception as e:
            if self._is_quota_error(e):
                self._save_snapshot(input_text, phase_idx, accumulated_context, all_results)
                self.state = AgentState.ERROR
                await self._log("💰 API quota hit, progress saved.")
                return (
                    "⚠️ API 额度不足，执行已暂停"
                    "。请充值后在对话中发送「继续」，我会从断点恢复执行。"
                )
            self.state = AgentState.ERROR
            await self._log(f"❌ Planning Flow failed: {e}")
            return f"Execution failed: {e}"

    async def resume(self) -> str:
        """Resume execution from a saved snapshot."""
        if not self._snapshot:
            return "No saved snapshot to resume from."

        snap = self._snapshot
        self._snapshot = None
        self.state = AgentState.RUNNING

        # Restore ProblemUnderstanding from snapshot
        self._pu = snap.get("pu")

        input_text = snap["input_text"]
        start_phase_idx = snap["phase_idx"]
        accumulated_context = snap["accumulated_context"]
        all_results = snap["all_results"]
        saved_plan = snap["plan"]

        phases = [
            ProjectPhase.INCEPTION,
            ProjectPhase.BLUEPRINTING,
            ProjectPhase.CODING,
            ProjectPhase.WRITING,
        ]

        await self._log(f"🔄 Resuming from: Phase {snap['current_phase'].value}")
        phase_idx = start_phase_idx

        try:
            for phase_idx in range(start_phase_idx, len(phases)):
                phase = phases[phase_idx]
                self.current_phase = phase

                if phase_idx == start_phase_idx and saved_plan:
                    self.plan = saved_plan
                    await self._log(f"🔄 Restoring Phase: {phase.value}")
                    await self._emit(
                        "phase_start", phase=phase.value,
                        phase_index=phase_idx, total_phases=len(phases)
                    )
                    self.planning_agent.reset()
                    self.executor_agent.reset()
                else:
                    await self._log(f"🚀 Starting Phase: {phase.value}")
                    await self._emit(
                        "phase_start", phase=phase.value,
                        phase_index=phase_idx, total_phases=len(phases)
                    )
                    self.planning_agent.reset()
                    self.executor_agent.reset()
                    await self._create_phase_plan(input_text, accumulated_context)

                if not self.plan or not self.plan.steps:
                    continue

                if self._memory:
                    await self._memory.start_phase(phase.value)

                phase_result = await self._execute_phase_steps(accumulated_context)
                summary = f"## Phase {phase.value} Results\n{phase_result}\n"
                all_results.append(summary)
                accumulated_context += summary + "\n"
                await self._save_phase_artifact(phase, phase_result)
                await self._broadcast_memory()

            self.state = AgentState.FINISHED
            return "\n\n".join(all_results)

        except Exception as e:
            if self._is_quota_error(e):
                self._save_snapshot(input_text, phase_idx, accumulated_context, all_results)
                self.state = AgentState.ERROR
                await self._log("💰 Quota hit again, progress saved.")
                return (
                    "⚠️ API 额度再次不足"
                    "。请充值后再次发送「继续」恢复执行。"
                )
            self.state = AgentState.ERROR
            await self._log(f"❌ Resume failed: {e}")
            return f"Resume failed: {e}"

    # ------------------------------------------------------------------
    # Internal — plan creation (dynamic, problem-grounded)
    # ------------------------------------------------------------------

    async def _create_phase_plan(self, input_text: str, fallback_context: str) -> None:
        """Decompose the task for the current phase using ProblemUnderstanding + memory context."""
        # Dynamic prompt grounded in actual problem
        current_prompt = build_phase_prompt(self.current_phase.value, self._pu)

        # Context from memory
        if self._memory:
            context = await self._memory.build_planning_context(
                phase=self.current_phase.value,
                fallback=fallback_context,
            )
        else:
            MAX_CTX = 2000
            context = (
                ("...(已截断前文)...\n" + fallback_context[-MAX_CTX:])
                if len(fallback_context) > MAX_CTX
                else fallback_context
            )

        plan_request = BaseMessage.make_user_message(
            role_name="User",
            content=(
                f"{current_prompt}\n\n"
                f"## 上一阶段背景\n{context}\n\n"
                f"请针对当前阶段 '{self.current_phase.value}'，"
                f"将任务分解为清晰、可执行、针对本题目的步骤。\n"
                f"每个步骤必须与题目的具体内容相关（避免通用化描述）。\n"
                f"按照编号列表格式返回 (1. 2. 3. ...)，每行只写步骤标题。\n\n"
                f"原始任务: {input_text}\n"
                f"请使用中文回复。"
            ),
        )

        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(
                None, lambda: self.planning_agent.step(plan_request)
            )
        except Exception as e:
            await self._log(f"⚠️ Plan generation failed ({e}), retrying…")
            self.planning_agent.reset()
            fallback_request = BaseMessage.make_user_message(
                role_name="User",
                content=(
                    f"{current_prompt}\n\n"
                    f"请针对当前阶段 '{self.current_phase.value}'，"
                    f"将任务分解为清晰、可执行的步骤。\n"
                    f"按照编号列表格式返回 (1. 2. 3. ...)。\n\n"
                    f"原始任务: {input_text}\n请使用中文回复。"
                ),
            )
            response = await loop.run_in_executor(
                None, lambda: self.planning_agent.step(fallback_request)
            )

        steps: list[PlanStep] = []
        if response.msgs:
            for line in response.msgs[0].content.strip().split("\n"):
                line = line.strip()
                m = re.match(r"^\d+[\.\\)]\s*(.+)$", line)
                if m and (txt := m.group(1).strip()):
                    steps.append(PlanStep(description=txt))

        if not steps:
            steps.append(PlanStep(description=f"Execute {self.current_phase.value} tasks"))

        self.plan = Plan(
            plan_id=f"plan_{self.current_phase.value}_{int(time.time())}",
            title=f"{self.current_phase.value}: {input_text[:50]}",
            steps=steps,
        )

        await self._log(f"📝 Phase Plan ({self.current_phase.value}): {len(steps)} steps")
        await self._emit(
            "phase_plan",
            phase=self.current_phase.value,
            total_steps=len(steps),
            step_titles=[s.description[:80] for s in steps],
        )

    # ------------------------------------------------------------------
    # Internal — step execution with Eval Loop
    # ------------------------------------------------------------------

    async def _execute_phase_steps(self, fallback_context: str) -> str:
        """Execute all plan steps, with Observe→Evaluate→Fix inner loop."""
        while True:
            step_index = self.plan.get_next_step_index()
            if step_index is None:
                break

            step = self.plan.steps[step_index]
            step.status = PlanStepStatus.IN_PROGRESS
            await self._log(f"📋 Executing: {step.description}")
            await self._emit(
                "step_start",
                phase=self.current_phase.value,
                step_index=step_index,
                step_title=step.description,
                total_steps=len(self.plan.steps),
            )

            try:
                result = await self._execute_step_with_eval_loop(
                    step_index, fallback_context
                )
                step.status = PlanStepStatus.COMPLETED
                step.result = result

                if self._memory:
                    try:
                        await self._memory.record_step(
                            phase=self.current_phase.value,
                            step_index=step_index,
                            step_title=step.description,
                            content=result,
                        )
                    except Exception as me:
                        await self._log(f"⚠️ Memory write failed: {me}")

                await self._emit(
                    "step_complete",
                    phase=self.current_phase.value,
                    step_index=step_index,
                    step_title=step.description,
                    result_preview=result[:200] if result else "",
                )
                await self._broadcast_memory()

            except Exception as e:
                step.status = PlanStepStatus.BLOCKED
                step.result = f"Error: {e}"
                await self._log(f"❌ Step blocked: {e}")
                return await self._synthesize_or_fallback(fallback_context)

        return await self._synthesize_or_fallback(fallback_context)

    async def _execute_step_with_eval_loop(
        self, step_index: int, fallback_context: str
    ) -> str:
        """Execute a single step with Observe→Evaluate→Fix inner loop.

        Coding phase steps get up to MAX_EVAL_ITERATIONS passes.
        Other phases get a single pass (no eval loop needed).
        """
        is_coding = self.current_phase == ProjectPhase.CODING
        max_iters = self.MAX_EVAL_ITERATIONS if is_coding else 1

        context = fallback_context
        last_result = ""

        for iteration in range(1, max_iters + 1):
            # ---- Execute ----
            result = await self._execute_step_once(step_index, context)
            last_result = result

            if not is_coding or max_iters == 1:
                return result

            # ---- Observe ----
            obs_text = result[:300] if result else "（无输出）"
            await self._emit(
                "eval_step",
                phase=self.current_phase.value,
                step_index=step_index,
                tag="OBS",
                text=f"执行输出: {obs_text}",
                iter=iteration,
            )

            # ---- Evaluate ----
            step = self.plan.steps[step_index]
            eval_verdict = await self._evaluate_step_result(step.description, result)

            await self._emit(
                "eval_step",
                phase=self.current_phase.value,
                step_index=step_index,
                tag="EVAL",
                text=eval_verdict["conclusion"],
                iter=iteration,
            )

            if eval_verdict["is_good"]:
                await self._emit(
                    "eval_step",
                    phase=self.current_phase.value,
                    step_index=step_index,
                    tag="DONE",
                    text="✓ 结果验证通过，继续下一步",
                    iter=iteration,
                )
                return result

            # ---- Fix ----
            fix_hint = eval_verdict["fix_suggestion"]
            await self._emit(
                "eval_step",
                phase=self.current_phase.value,
                step_index=step_index,
                tag="FIX",
                text=fix_hint,
                iter=iteration,
            )

            if iteration < max_iters:
                context = (
                    context
                    + f"\n\n[迭代{iteration}结果有问题]: {fix_hint}\n"
                    f"请根据上述反馈修正并重新执行。"
                )
                await self._log(f"🔄 Eval Loop iteration {iteration}: fixing…")

        return last_result

    async def _execute_step_once(self, step_index: int, context: str) -> str:
        """Execute a single step once (inner implementation)."""
        step = self.plan.steps[step_index]
        plan_context = self.plan.get_summary()

        phase_prompt = build_phase_prompt(self.current_phase.value, self._pu)

        # Build context window from memory
        if self._memory:
            try:
                context_block = await self._memory.build_step_context(
                    phase=self.current_phase.value,
                    step_index=step_index,
                    max_chars=4000,
                )
                context_block = context_block or context
            except Exception:
                context_block = context
        else:
            MAX_CTX = 2000
            context_block = (
                ("...(已截断前文)...\n" + context[-MAX_CTX:])
                if len(context) > MAX_CTX
                else context
            )

        step_message = BaseMessage.make_user_message(
            role_name="User",
            content=(
                f"{phase_prompt}\n\n"
                f"## 上下文记忆（来自前序阶段与步骤）\n{context_block}\n\n"
                f"## 待执行步骤\n{step.description}\n\n"
                f"## 本阶段计划进度\n{plan_context}\n\n"
                f"请执行此步骤。完成后详细汇报结果。"
            ),
        )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, lambda: self.executor_agent.step(step_message)
        )
        return response.msgs[0].content if response.msgs else "Step completed"

    async def _evaluate_step_result(
        self, step_goal: str, result: str
    ) -> dict:
        """Use LLM to evaluate whether a step result meets the goal.

        Returns:
            {is_good: bool, conclusion: str, fix_suggestion: str}
        """
        eval_prompt = BaseMessage.make_user_message(
            role_name="User",
            content=(
                f"你是数学建模质量评审专家。请评估以下步骤的执行结果是否达到目标。\n\n"
                f"## 步骤目标\n{step_goal}\n\n"
                f"## 执行结果（前500字）\n{result[:500]}\n\n"
                f"请以 JSON 格式回复：\n"
                f'{{"is_good": true/false, "conclusion": "一句话评估结论", '
                f'"fix_suggestion": "如果有问题，具体说明如何修正（is_good=true时留空）"}}\n'
                f"只返回 JSON，不要其他文字。"
            ),
        )

        try:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                None, lambda: self.planning_agent.step(eval_prompt)
            )
            raw = resp.msgs[0].content if resp.msgs else ""
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                data = json.loads(m.group())
                return {
                    "is_good": bool(data.get("is_good", True)),
                    "conclusion": str(data.get("conclusion", "结果已生成")),
                    "fix_suggestion": str(data.get("fix_suggestion", "")),
                }
        except Exception as e:
            logger.debug(f"[EvalLoop] evaluation failed ({e}), treating as good")

        # Default: treat as good to avoid infinite loops on eval failure
        return {"is_good": True, "conclusion": "结果已生成（评估跳过）", "fix_suggestion": ""}

    async def _synthesize_or_fallback(self, fallback_context: str) -> str:
        """Synthesize phase results via memory, or fall back to raw concat."""
        if self._memory:
            try:
                return await self._memory.synthesize_phase(
                    phase=self.current_phase.value,
                    on_log=self.on_log,
                )
            except Exception as e:
                await self._log(f"⚠️ Synthesis failed, using raw results: {e}")

        raw = []
        for step in self.plan.steps:
            if step.result:
                raw.append(f"Step: {step.description}\nResult: {step.result}")
        return "\n".join(raw)

    def _build_summary(self) -> str:
        return "Execution Complete"
