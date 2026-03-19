"""Pydantic request/response schemas for API endpoints.

This module is a legacy compatibility copy. The active import target in this
project is the `app.schemas` package (`backend/app/schemas/__init__.py`). Keep
shared definitions aligned until the duplicate module is removed.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str
    competition: str = "MCM"


class ProjectResponse(BaseModel):
    project_id: uuid.UUID
    title: str
    competition: str
    status: str
    created_at: datetime
    timeline: List[dict[str, Any]] = Field(default_factory=list)
    phase_confirm: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}
