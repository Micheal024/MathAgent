"""Tool infrastructure — wraps Python functions as Camel AI OpenAIFunction tools.

In Camel AI, tools are defined as plain Python functions with clear docstrings.
They are then wrapped with `OpenAIFunction(func)` for the ChatAgent to use.

This module provides:
- Helper utilities for creating OpenAIFunction tools
- ToolRegistry for managing all available tools
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from app.camel_compat import OpenAIFunction
from loguru import logger


class ToolRegistry:
    """Registry for managing all available tools.

    Usage:
        registry = ToolRegistry()
        registry.register(my_function)
        tools = registry.get_tools()  # List[OpenAIFunction]
    """

    def __init__(self):
        self._tools: Dict[str, OpenAIFunction] = {}

    def register(
        self,
        func: Callable,
        openai_tool_schema: Optional[Dict[str, Any]] = None,
    ) -> OpenAIFunction:
        """Register a function as a tool.

        Args:
            func: The callable function to register.
            openai_tool_schema: Optional custom schema override.

        Returns:
            The created OpenAIFunction.
        """
        tool = OpenAIFunction(func=func, openai_tool_schema=openai_tool_schema)
        name = tool.get_function_name()
        self._tools[name] = tool
        logger.debug(f"Registered tool: {name}")
        return tool

    def register_all(self, *funcs: Callable) -> List[OpenAIFunction]:
        """Register multiple functions as tools."""
        return [self.register(f) for f in funcs]

    def get_tools(self) -> List[OpenAIFunction]:
        """Get all registered tools as a list."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[OpenAIFunction]:
        """Get a specific tool by name."""
        return self._tools.get(name)

    @property
    def tool_names(self) -> List[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())
