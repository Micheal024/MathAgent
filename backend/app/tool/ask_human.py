"""T9: AskHuman — Request input from the user.

Used at Gate checkpoints and when the agent needs clarification.
In production, this sends a WebSocket message and waits for the user's response.
In development/testing, it returns a placeholder.

PRD §2.7: Input: `question: str` → Output: `user_response: str`
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from app.context import project_id_var
from app.interaction import InteractionManager

def ask_human(question: str) -> str:
    """Ask the user a question and wait for their response.

    Use this tool when you need user confirmation on important decisions,
    such as choosing between modeling strategies, approving a plan,
    or requesting additional information.

    Args:
        question: The question to ask the user.

    Returns:
        The user's response as a string.
    """
    logger.info(f"🙋 AskHuman: {question}")

    project_id = project_id_var.get()
    if not project_id:
        # Fallback if context is missing (e.g. testing)
        return "Error: Project context missing. Cannot ask user."

    # Use InteractionManager to request input (blocks this thread)
    try:
        response = InteractionManager.request_input_sync(project_id, question)
        return response
    except Exception as e:
        logger.error(f"AskHuman failed: {e}")
        return f"Error waiting for user response: {e}"
