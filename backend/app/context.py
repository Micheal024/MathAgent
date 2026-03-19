"""Context variables for request-scoped state."""

from contextvars import ContextVar
from typing import Optional

project_id_var: ContextVar[Optional[str]] = ContextVar("project_id", default=None)
