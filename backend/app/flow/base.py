"""BaseFlow — Abstract base class for execution flows."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseFlow(ABC):
    """Base class for orchestration flows."""

    @abstractmethod
    async def execute(self, input_text: str) -> str:
        """Execute the flow with the given input."""
