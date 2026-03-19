"""Core schema definitions for the Agent system.

Contains enums and data structures that complement Camel AI's built-in types.
Camel AI provides: ChatAgent, BaseMessage, OpenAIFunction, AgentMemory.
We provide: AgentState, PlanStepStatus, PlanningFlow state tracking.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# --- Enums ---

class AgentState(str, Enum):
    """Agent execution states (PRD §2.6.2)."""
    IDLE = "idle"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"


class ProjectPhase(str, Enum):
    """Project phases (PRD §2.6.2)."""
    INCEPTION = "inception"
    BLUEPRINTING = "blueprinting"
    CODING = "coding"
    WRITING = "writing"
    COMPLETED = "completed"


class PlanStepStatus(str, Enum):
    """Plan step execution states (PRD §2.6.3)."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

    @classmethod
    def get_active_statuses(cls) -> list:
        return [cls.NOT_STARTED.value, cls.IN_PROGRESS.value]

    @classmethod
    def get_status_marks(cls) -> dict:
        return {
            cls.COMPLETED.value: "[✓]",
            cls.IN_PROGRESS.value: "[→]",
            cls.BLOCKED.value: "[!]",
            cls.NOT_STARTED.value: "[ ]",
        }


class PlanStep(BaseModel):
    """A single step in a plan."""
    description: str
    status: PlanStepStatus = PlanStepStatus.NOT_STARTED
    result: Optional[str] = None


class Plan(BaseModel):
    """A plan consisting of multiple steps."""
    plan_id: str
    title: str
    steps: List[PlanStep] = Field(default_factory=list)

    def get_next_step_index(self) -> Optional[int]:
        """Get the index of the next step to execute."""
        for i, step in enumerate(self.steps):
            if step.status in (PlanStepStatus.NOT_STARTED, PlanStepStatus.IN_PROGRESS):
                return i
        return None

    def get_summary(self) -> str:
        """Get a formatted summary of plan progress."""
        marks = PlanStepStatus.get_status_marks()
        lines = []
        for i, step in enumerate(self.steps):
            mark = marks.get(step.status.value, "[ ]")
            lines.append(f"{mark} {i + 1}. {step.description}")
        return "\n".join(lines)

    @property
    def completed_count(self) -> int:
        return sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)

    @property
    def is_complete(self) -> bool:
        return all(
            s.status in (PlanStepStatus.COMPLETED, PlanStepStatus.BLOCKED)
            for s in self.steps
        )
