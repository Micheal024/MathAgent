"""Lightweight workflow smoke tests."""

from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.workflow import router as workflow_router
from app.schemas import ProjectResponse
from app.ws.handler import get_project_runtime_state


app = FastAPI()
app.include_router(workflow_router, prefix="/api/v1")
client = TestClient(app)


def test_project_response_includes_phase_confirm() -> None:
    project = ProjectResponse(
        project_id=uuid.uuid4(),
        title="Mock Project",
        competition="MCM",
        status="inception",
        created_at="2026-03-09T00:00:00Z",
        phase_confirm={"phase": "inception", "summary": "ok"},
    )

    assert project.phase_confirm == {"phase": "inception", "summary": "ok"}


def test_runtime_state_defaults_to_idle() -> None:
    runtime = get_project_runtime_state(str(uuid.uuid4()))

    assert runtime["status"] == "idle"
    assert runtime["connected_clients"] == 0
    assert runtime["has_active_flow"] is False
    assert runtime["can_resume"] is False
    assert runtime["waiting_for_phase_confirm"] is False


def test_workflow_status_endpoint_reports_idle() -> None:
    project_id = uuid.uuid4()

    response = client.get(f"/api/v1/workflow/{project_id}")

    assert response.status_code == 200
    assert response.json()["project_id"] == str(project_id)
    assert response.json()["status"] == "idle"


def test_start_workflow_requires_websocket_connection() -> None:
    response = client.post(
        "/api/v1/workflow/start",
        json={"project_id": str(uuid.uuid4())},
    )

    assert response.status_code == 409
    assert "WebSocket connection" in response.json()["detail"]


def test_stop_workflow_returns_idle_without_active_task() -> None:
    project_id = uuid.uuid4()

    response = client.post(
        "/api/v1/workflow/stop",
        json={"project_id": str(project_id)},
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": str(project_id),
        "status": "idle",
        "detail": "No active workflow task.",
    }
