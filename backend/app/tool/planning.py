"""T11: Planning — Create and manage execution plans.

Provides plan lifecycle management for PlanningFlow:
  - create: Create a new plan with steps
  - update: Modify plan steps
  - mark: Mark a step's status
  - list: View current plan state

PRD §2.7: Input: `command, plan_id, steps?` → Output: `plan_status`
"""

from __future__ import annotations

import json
import time
from typing import Optional

from loguru import logger

from app.schema import Plan, PlanStep, PlanStepStatus

# In-memory plan store (will be persisted to DB in M3)
_plans: dict[str, Plan] = {}


def planning(
    command: str,
    plan_id: str = "",
    title: str = "",
    steps: str = "",
    step_index: int = -1,
    step_status: str = "",
) -> str:
    """Manage task execution plans.

    Use this tool to create, update, and track multi-step plans
    for complex math modeling tasks.

    Commands:
        create: Create a new plan (provide title and steps as JSON array)
        list: View the current plan status
        mark: Mark a step's status (provide step_index and step_status)
        update: Update a step's description (provide step_index and steps)

    Args:
        command: The operation ("create", "list", "mark", "update").
        plan_id: Identifier for the plan.
        title: Plan title (used with "create" command).
        steps: JSON array of step descriptions, or single step text for update.
        step_index: Index of the step to modify (0-based).
        step_status: New status ("not_started", "in_progress", "completed", "blocked").

    Returns:
        A formatted plan status or confirmation message.
    """
    if command == "create":
        return _create_plan(title, steps)
    elif command == "list":
        return _list_plan(plan_id)
    elif command == "mark":
        return _mark_step(plan_id, step_index, step_status)
    elif command == "update":
        return _update_step(plan_id, step_index, steps)
    else:
        return f"[error] Unknown command: {command}. Use 'create', 'list', 'mark', or 'update'."


def _create_plan(title: str, steps_json: str) -> str:
    """Create a new plan."""
    try:
        step_descriptions = json.loads(steps_json) if steps_json else []
    except json.JSONDecodeError:
        # Try splitting by newlines
        step_descriptions = [s.strip() for s in steps_json.split("\n") if s.strip()]

    if not step_descriptions:
        return "[error] No steps provided. Pass steps as a JSON array or newline-separated text."

    plan_id = f"plan_{int(time.time())}"
    plan = Plan(
        plan_id=plan_id,
        title=title or "Untitled Plan",
        steps=[PlanStep(description=desc) for desc in step_descriptions],
    )
    _plans[plan_id] = plan

    logger.info(f"📝 Created plan '{plan_id}' with {len(plan.steps)} steps")
    return f"Plan created: {plan_id}\n{plan.get_summary()}"


def _list_plan(plan_id: str) -> str:
    """List plan status."""
    if plan_id and plan_id in _plans:
        plan = _plans[plan_id]
        return f"Plan: {plan.title} ({plan.plan_id})\n{plan.get_summary()}"

    if _plans:
        parts = []
        for pid, plan in _plans.items():
            parts.append(f"## {plan.title} ({pid})\n{plan.get_summary()}")
        return "\n\n".join(parts)

    return "No plans found."


def _mark_step(plan_id: str, step_index: int, status_str: str) -> str:
    """Mark a step's status."""
    if plan_id not in _plans:
        return f"[error] Plan not found: {plan_id}"

    plan = _plans[plan_id]
    if step_index < 0 or step_index >= len(plan.steps):
        return f"[error] Step index {step_index} out of range (0-{len(plan.steps) - 1})"

    try:
        new_status = PlanStepStatus(status_str)
    except ValueError:
        valid = ", ".join(s.value for s in PlanStepStatus)
        return f"[error] Invalid status '{status_str}'. Valid: {valid}"

    plan.steps[step_index].status = new_status
    logger.info(f"📋 Step {step_index} → {new_status.value}")
    return f"Step {step_index} marked as {new_status.value}\n{plan.get_summary()}"


def _update_step(plan_id: str, step_index: int, new_description: str) -> str:
    """Update a step's description."""
    if plan_id not in _plans:
        return f"[error] Plan not found: {plan_id}"

    plan = _plans[plan_id]
    if step_index < 0 or step_index >= len(plan.steps):
        return f"[error] Step index {step_index} out of range"

    old = plan.steps[step_index].description
    plan.steps[step_index].description = new_description
    logger.info(f"✏️ Step {step_index} updated: '{old}' → '{new_description}'")
    return f"Step {step_index} updated\n{plan.get_summary()}"
