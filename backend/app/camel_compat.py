"""Camel AI compatibility layer.

camel-ai v0.1.6's `camel.toolkits.__init__` eagerly imports all toolkits,
including ones requiring optional dependencies (unstructured, etc.).

This module provides direct access to the specific Camel AI components
we need without triggering the full import chain.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Callable, Dict, Optional


def _load_module_direct(module_name: str, file_path: str):
    """Load a Python module directly from file, bypassing __init__.py."""
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _get_camel_path() -> str:
    """Get the camel package installation path."""
    import camel
    return os.path.dirname(camel.__file__)


def get_openai_function_class():
    """Get the FunctionTool class without triggering full toolkits import.

    camel-ai >= 0.2.x renamed OpenAIFunction -> FunctionTool in
    camel/toolkits/function_tool.py. We load it directly to avoid the
    toolkits __init__.py eagerly importing all optional dependencies.
    We alias FunctionTool as OpenAIFunction for backward compatibility.
    """
    camel_path = _get_camel_path()

    # Load camel.utils first (dependency of function_tool)
    utils_path = os.path.join(camel_path, "utils", "__init__.py")
    _load_module_direct("camel.utils", utils_path)

    # camel-ai >= 0.2.x: FunctionTool in function_tool.py
    ft_path = os.path.join(camel_path, "toolkits", "function_tool.py")
    if os.path.exists(ft_path):
        mod = _load_module_direct("camel.toolkits.function_tool", ft_path)
        return mod.FunctionTool

    # camel-ai < 0.2.x fallback: OpenAIFunction in openai_function.py
    of_path = os.path.join(camel_path, "toolkits", "openai_function.py")
    mod = _load_module_direct("camel.toolkits.openai_function", of_path)
    return mod.OpenAIFunction


# Pre-load the class so other modules can import directly
try:
    OpenAIFunction = get_openai_function_class()
except ImportError:
    # Fallback: if camel not installed, provide a stub
    OpenAIFunction = None  # type: ignore
