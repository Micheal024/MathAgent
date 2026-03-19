"""Artifacts API endpoints."""

from __future__ import annotations

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db
from app.models.project import Artifact

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{project_id}")
async def list_artifacts(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """List artifacts for a project."""
    try:
        stmt = (
            select(Artifact)
            .where(Artifact.project_id == project_id)
            .order_by(Artifact.created_at.desc())
        )
        result = await db.execute(stmt)
        artifacts = result.scalars().all()
        
        return [
            {
                "id": str(a.id),
                "type": a.artifact_type,
                "content": a.content,
                "version": a.version,
                "frozen": a.frozen,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in artifacts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
