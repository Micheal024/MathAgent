"""Workflow API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas import (
    WorkflowResponse,
    WorkflowStart,
    WorkflowStatusResponse,
    WorkflowStopRequest,
)
from app.ws.handler import get_project_runtime_state, stop_project_execution

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/{project_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(project_id: UUID):
    """Return the live runtime state for a project's agent workflow."""
    runtime = get_project_runtime_state(str(project_id))
    return WorkflowStatusResponse(project_id=project_id, **runtime)


@router.post("/start", response_model=WorkflowResponse)
async def start_workflow(payload: WorkflowStart):
    """Validate whether a project is ready to start over WebSocket."""
    runtime = get_project_runtime_state(str(payload.project_id))

    if runtime["connected_clients"] == 0:
        raise HTTPException(
            status_code=409,
            detail="Workflow execution requires an active WebSocket connection.",
        )

    detail = "Send a WebSocket `user_message` to begin execution."
    if runtime["status"] == "running":
        detail = "Workflow is already running for this project."
    elif runtime["can_resume"]:
        detail = "Checkpoint is available; send `继续` over WebSocket to resume."

    return WorkflowResponse(
        task_id=str(payload.project_id),
        status=runtime["status"],
        detail=detail,
    )


@router.post("/stop", response_model=WorkflowResponse)
async def stop_workflow(payload: WorkflowStopRequest):
    """Stop a running project workflow if one exists."""
    stopped = await stop_project_execution(str(payload.project_id))
    return WorkflowResponse(
        task_id=str(payload.project_id),
        status="stopped" if stopped else "idle",
        detail="Workflow cancelled." if stopped else "No active workflow task.",
    )
