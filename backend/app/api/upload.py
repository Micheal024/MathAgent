"""File upload API endpoint.

Handles multipart file uploads, saves to workspace/uploads/,
and returns parsed content.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger

from app.config import config
from app.tool.file_parser import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    get_file_category,
    parse_file,
)

router = APIRouter(prefix="/upload", tags=["upload"])

# Ensure uploads directory exists
UPLOADS_DIR = Path(config.workspace_root) / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """Upload and parse a file (PDF, image, or text).

    Returns the parsed content plus file metadata.
    """
    # --- Validate filename ---
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # --- Read and validate size ---
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(contents)} bytes). Maximum: {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    # --- Save to disk ---
    file_id = str(uuid.uuid4())[:8]
    safe_name = f"{file_id}_{file.filename}"
    save_path = UPLOADS_DIR / safe_name
    save_path.write_bytes(contents)
    logger.info(f"File saved: {save_path} ({len(contents)} bytes)")

    # --- Parse ---
    try:
        result = parse_file(str(save_path))
    except Exception as e:
        logger.error(f"Parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {e}")

    return {
        "file_id": file_id,
        "filename": file.filename,
        "file_type": get_file_category(file.filename) or "unknown",
        "size": len(contents),
        "content": result.get("content", ""),
        "parsed": result.get("success", False),
        "metadata": {
            k: v
            for k, v in result.items()
            if k not in ("content", "success", "error", "file_type", "filename", "size")
        },
        "error": result.get("error"),
    }
