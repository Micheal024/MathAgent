"""T3: StrReplaceEditor — Create and edit files.

Supports three commands:
  - create: Create a new file with content
  - str_replace: Replace text in an existing file
  - view: View file contents

PRD §2.7: Input: `path, content/old_str/new_str` → Output: `success/error`
"""

from __future__ import annotations

import os

from loguru import logger

from app.config import config


def str_replace_editor(
    command: str,
    path: str,
    content: str = "",
    old_str: str = "",
    new_str: str = "",
    view_range: str = "",
) -> str:
    """Create, edit, or view files in the workspace.

    Use this tool to write code files, LaTeX documents, data files,
    and any other text files needed for the math modeling project.

    Commands:
        create: Create a new file with the given content
        str_replace: Replace old_str with new_str in the file
        view: View the contents of a file

    Args:
        command: The operation to perform ("create", "str_replace", or "view").
        path: Relative path to the file within the workspace directory.
        content: File content (used with "create" command).
        old_str: Text to find (used with "str_replace" command).
        new_str: Replacement text (used with "str_replace" command).
        view_range: Optional line range "start:end" (used with "view" command).

    Returns:
        A success message or the file contents (for view), or an error message.
    """
    workspace = config.workspace_root
    full_path = os.path.join(workspace, path)

    # Security: ensure path is within workspace
    real_workspace = os.path.realpath(workspace)
    real_path = os.path.realpath(full_path)
    if not real_path.startswith(real_workspace):
        return f"[error] Path '{path}' is outside the workspace directory"

    if command == "create":
        return _create_file(full_path, content)
    elif command == "str_replace":
        return _str_replace(full_path, old_str, new_str)
    elif command == "view":
        return _view_file(full_path, view_range)
    else:
        return f"[error] Unknown command: {command}. Use 'create', 'str_replace', or 'view'."


def _create_file(full_path: str, content: str) -> str:
    """Create a new file with content."""
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"📝 Created: {full_path}")
        return f"File created successfully: {full_path}"
    except Exception as e:
        return f"[error] Failed to create file: {e}"


def _str_replace(full_path: str, old_str: str, new_str: str) -> str:
    """Replace text in an existing file."""
    if not os.path.exists(full_path):
        return f"[error] File not found: {full_path}"

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_str not in content:
            return f"[error] String not found in file: '{old_str[:50]}...'"

        count = content.count(old_str)
        new_content = content.replace(old_str, new_str)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"✏️ Updated: {full_path} ({count} replacement(s))")
        return f"Successfully replaced {count} occurrence(s) in {full_path}"
    except Exception as e:
        return f"[error] Failed to edit file: {e}"


def _view_file(full_path: str, view_range: str) -> str:
    """View file contents."""
    if not os.path.exists(full_path):
        return f"[error] File not found: {full_path}"

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if view_range:
            parts = view_range.split(":")
            start = max(0, int(parts[0]) - 1) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else len(lines)
            lines = lines[start:end]
            header = f"[{full_path}] Lines {start + 1}-{min(end, len(lines) + start)}\n"
        else:
            header = f"[{full_path}] ({len(lines)} lines)\n"

        # Limit output size
        content = "".join(lines[:200])
        if len(lines) > 200:
            content += f"\n... ({len(lines) - 200} more lines truncated)"

        return header + content
    except Exception as e:
        return f"[error] Failed to read file: {e}"
