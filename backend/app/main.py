"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    if not config.auth.secret_key:
        raise RuntimeError("AUTH_SECRET_KEY environment variable must be set")

    logger.info(f"🚀 Starting {config.app_name} v0.1.0")
    logger.info(f"📂 Workspace: {config.workspace_root}")
    
    # Initialize DB (create tables) for Dev/SQLite
    from app.models.database import engine, Base
    # Import models to ensure they are registered
    from app.models import user, project

    async with engine.begin() as conn:
        # Enable foreign keys for SQLite (must run per-connection via async engine)
        if config.database.url.startswith("sqlite"):
            from sqlalchemy import text
            await conn.execute(text("PRAGMA foreign_keys=ON"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    logger.info("👋 Shutting down")


app = FastAPI(
    title=config.app_name,
    description="数学建模智能 Agent — 对标 Manus/OpenManus 架构",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": config.app_name, "version": "0.1.0"}


# --- API Routers ---
from app.api import projects, chat, workflow, artifacts, upload
app.include_router(projects.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(artifacts.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")

# --- WebSocket ---
from app.ws.handler import ws_router
app.include_router(ws_router)
