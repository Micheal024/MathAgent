# Pydantic schemas
"""Pydantic request/response schemas for API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Project Schemas ---

class ProjectCreate(BaseModel):
    title: str
    competition: str = "MCM"


class ProjectResponse(BaseModel):
    project_id: uuid.UUID
    title: str
    competition: str
    status: str
    created_at: datetime
    timeline: list = Field(default_factory=list)
    phase_confirm: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


# --- Chat Schemas ---

class ChatSend(BaseModel):
    session_id: Optional[str] = None
    content: str
    mention: Optional[str] = None


class ChatMessageResponse(BaseModel):
    msg_id: str
    status: str = "sent"


# --- Workflow Schemas ---

class WorkflowStart(BaseModel):
    project_id: uuid.UUID
    phase: Optional[str] = None
    content: Optional[str] = None


class WorkflowResponse(BaseModel):
    task_id: str
    status: str = "started"
    detail: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    project_id: uuid.UUID
    status: str
    connected_clients: int = 0
    has_active_flow: bool = False
    can_resume: bool = False
    waiting_for_phase_confirm: bool = False


class WorkflowStopRequest(BaseModel):
    project_id: uuid.UUID


# --- Gate Schemas ---

class GateDecision(BaseModel):
    task_id: str
    decision: str  # "approve" | "reject" | "revise"
    feedback: Optional[str] = None


class GateResponse(BaseModel):
    next_state: str


# --- Code Execution Schemas ---

class CodeExecuteRequest(BaseModel):
    code: str


class CodeExecuteResponse(BaseModel):
    stdout: str = ""
    stderr: str = ""
    figures: list[str] = Field(default_factory=list)


# --- Export Schemas ---

class ExportRequest(BaseModel):
    format: str = "pdf"  # "pdf" | "docx" | "latex"


class ExportResponse(BaseModel):
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None
    latex_url: Optional[str] = None
