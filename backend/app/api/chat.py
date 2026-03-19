"""Chat API endpoints."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db
from app.models.project import ChatLog

router = APIRouter()


@router.get("/project/{project_id}/history")
async def get_chat_history(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get chat history for a project."""
    try:
        stmt = (
            select(ChatLog)
            .where(ChatLog.project_id == project_id)
            .order_by(ChatLog.created_at.asc())
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        formatted_logs = []
        for log in logs:
            # Map DB types to Frontend types
            msg_type = log.msg_type
            if msg_type == "result":
                msg_type = "assistant_message"
            elif msg_type == "user_input":
                msg_type = "user_message"
            elif msg_type == "gate":
                msg_type = "ask_human"
            elif msg_type == "code":
                msg_type = "tool_call"
            # "thought" remains "thought"
                
            formatted_logs.append({
                "id": str(log.id),
                "sender": log.sender,
                "content": log.content,
                "type": msg_type,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                **(log.metadata_json or {})
            })

        return formatted_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
