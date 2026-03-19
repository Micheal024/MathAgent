"""MathModelingAgent — Creates a Camel AI ChatAgent for math modeling tasks.

Architecture:
    Camel AI ChatAgent (core LLM + tool calling + memory)
    + Custom PlanningFlow (OpenManus-inspired orchestration)
    = MathModelingAgent

This module provides factory functions to create configured ChatAgent instances:
    - create_math_modeling_agent() → ChatAgent with math modeling tools
    - create_planning_agent() → ChatAgent for plan generation

The ChatAgent handles:
    - LLM interaction (via Camel's built-in model backends)
    - Tool calling (via OpenAIFunction)
    - Memory / message management
    - Structured output

We do NOT subclass ChatAgent — we configure it.
"""

from __future__ import annotations

from typing import List, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from app.camel_compat import OpenAIFunction
from app.config import config
from app.prompt.math_modeling import SYSTEM_PROMPT
from app.tool.base import ToolRegistry
from app.tool.terminate import terminate


PROVIDER_SETTINGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "default_model": "abab6.5-chat",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-max",
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-pro-32k", # NOTE: User must replace this with their Endpoint ID
    },
}

def _create_model_backend():
    """Create a Camel model backend from our app config.

    Supports multiple providers via OpenAI-compatible interface.
    """
    api_key = config.llm.api_key
    provider = config.llm.provider.lower()
    
    # Get provider settings
    settings = PROVIDER_SETTINGS.get(provider, PROVIDER_SETTINGS["openai"])
    
    # Use config values if set customized, otherwise use provider defaults
    base_url = config.llm.base_url
    model_name = config.llm.model

    # If config is still default, switch to provider defaults
    if base_url == "https://api.openai.com/v1" and provider != "openai":
         base_url = settings["base_url"]
    
    if model_name == "gpt-4o" and provider != "openai":
         model_name = settings["default_model"]

    if not api_key or api_key.startswith("sk-your-"):
        # No valid API key — use stub for testing
        return ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=ModelType.STUB,
            model_config_dict={},
        )

    # All these providers are OpenAI-compatible
    # Camel's OPENAI_COMPATIBLE_MODEL type handles custom base_url

    platform = ModelPlatformType.OPENAI if (provider == "openai" and "openai.com" in base_url) else ModelPlatformType.OPENAI_COMPATIBLE_MODEL

    # For native OpenAI, we map model_type enum. For others, string is fine.
    model_type_arg = _get_openai_model_type(model_name) if platform == ModelPlatformType.OPENAI else model_name

    return ModelFactory.create(
        model_platform=platform,
        model_type=model_type_arg,
        model_config_dict={
            "max_tokens": config.llm.max_tokens,
            "temperature": config.llm.temperature,
        },
        api_key=api_key,
        url=base_url if platform == ModelPlatformType.OPENAI_COMPATIBLE_MODEL else None,
    )


def _get_openai_model_type(model_name: str) -> ModelType:
    """Map a model name string to Camel's ModelType enum."""
    mapping = {
        "gpt-4o": ModelType.GPT_4O,
        "gpt-4o-mini": ModelType.GPT_4O_MINI,
        "gpt-4-turbo": ModelType.GPT_4_TURBO,
        "gpt-4": ModelType.GPT_4,
        "gpt-3.5-turbo": ModelType.GPT_3_5_TURBO,
    }
    return mapping.get(model_name, ModelType.GPT_4O)


def _create_tool_registry() -> ToolRegistry:
    """Create and populate the tool registry with all available tools."""
    registry = ToolRegistry()

    # Core tools (always available)
    registry.register(terminate)

    # --- M2 Tools ---
    from app.tool.python_execute import python_execute
    from app.tool.ask_human import ask_human
    from app.tool.str_replace_editor import str_replace_editor
    from app.tool.planning import planning
    from app.tool.search_literature import search_literature
    from app.tool.classify_problem import classify_problem
    from app.tool.query_math_kg import query_math_kg
    from app.tool.latex_compile import latex_compile
    from app.tool.compliance_check import compliance_check

    registry.register_all(
        python_execute,
        ask_human,
        str_replace_editor,
        planning,
        search_literature,
        classify_problem,
        query_math_kg,
        latex_compile,
        compliance_check,
    )

    return registry


def create_math_modeling_agent(
    extra_tools: Optional[List[OpenAIFunction]] = None,
) -> ChatAgent:
    """Create a Camel AI ChatAgent configured for math modeling.

    This is the main agent used by PlanningFlow to execute each step.

    Args:
        extra_tools: Additional tools to include beyond the defaults.

    Returns:
        A configured ChatAgent instance.
    """
    # System message
    system_message = BaseMessage.make_assistant_message(
        role_name="MathModeler",
        content=SYSTEM_PROMPT.format(directory=config.workspace_root),
    )

    # Tools
    registry = _create_tool_registry()
    tools = registry.get_tools()
    if extra_tools:
        tools.extend(extra_tools)

    # Model backend (from config)
    model = _create_model_backend()

    # Create ChatAgent
    agent = ChatAgent(
        system_message=system_message,
        model=model,
        tools=tools,
    )

    return agent


def create_planning_agent() -> ChatAgent:
    """Create a ChatAgent specifically for plan generation.

    This agent is used by PlanningFlow to decompose tasks into steps.
    It has no tools — it only generates text plans.

    Returns:
        A configured ChatAgent for planning.
    """
    system_message = BaseMessage.make_assistant_message(
        role_name="Planner",
        content=(
            "你是一个任务规划专家。你的职责是将复杂的数学建模任务分解为清晰、可执行的步骤。\n"
            "每个步骤应该是具体且独立可执行的。\n"
            "按照数学建模的标准流程规划：破题→策划→编码→论文。\n"
            "返回编号列表格式 (1. 2. 3. ...)。"
        ),
    )

    model = _create_model_backend()

    return ChatAgent(system_message=system_message, model=model)
