"""Terminate tool — Signals task completion.

Defined as a plain function (Camel AI style), wrapped by OpenAIFunction.
"""

from __future__ import annotations


def terminate(status: str = "Task completed") -> str:
    """End the current task and provide a final summary.

    Call this tool when you have completed the assigned task
    or have no further actions to take.

    Args:
        status: Final status message summarizing what was accomplished.

    Returns:
        A confirmation message with the status.
    """
    return f"Task terminated: {status}"
