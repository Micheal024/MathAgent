"""Projects API endpoints."""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.context import CryptContext

from app.models.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas import ProjectCreate, ProjectResponse

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    # user_id: uuid.UUID = Depends(get_current_user_id) # Pending auth impl
):
    """Create a new math modeling project."""
    # Hardcoded user ID for M3 dev mode
    # user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    # In M3 we assume a default user exists or we create one
    
    # Check if we have a default user, if not create one
    result = await db.execute(select(User).limit(1))
    user = result.scalars().first()
    if not user:
        user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            email="demo@example.com",
            name="Demo User",
            hashed_password=_pwd_context.hash("demo"),
            role="student"
        )
        db.add(user)
        await db.commit()
    
    new_project = Project(
        title=project.title,
        competition=project.competition,
        user_id=user.id,
        status="inception"
    )
    
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    return ProjectResponse(
        project_id=new_project.id,
        title=new_project.title,
        competition=new_project.competition,
        status=new_project.status,
        created_at=new_project.created_at
    )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
):
    """List all projects."""
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    
    return [
        ProjectResponse(
            project_id=p.id,
            title=p.title,
            competition=p.competition,
            status=p.status,
            created_at=p.created_at,
            timeline=p.shared_context.get("timeline", []) if p.shared_context else [],
            phase_confirm=p.shared_context.get("phase_confirm") if p.shared_context else None,
        )
        for p in projects
    ]


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all its related data."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        project_id=project.id,
        title=project.title,
        competition=project.competition,
        status=project.status,
        created_at=project.created_at,
        timeline=project.shared_context.get("timeline", []) if project.shared_context else [],
        phase_confirm=project.shared_context.get("phase_confirm") if project.shared_context else None,
    )
