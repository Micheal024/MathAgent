"""Project, AgentSession, ChatLog, Artifact, MemoryItem models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Float, Integer, String, Text, Boolean
from sqlalchemy.types import Uuid as UUID, JSON
JSONB = JSON # Compatibility alias
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Project(Base):
    """Math modeling project (PRD §3.9)."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    competition: Mapped[str] = mapped_column(
        Enum("MCM", "ICM", "CUMCM", "APMCM", "IMMC", "other", name="competition_type"),
        default="MCM",
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "inception", "blueprinting", "coding", "writing", "completed",
            name="project_status",
        ),
        default="inception",
    )
    shared_context: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="projects")
    sessions = relationship("AgentSession", back_populates="project", lazy="selectin", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", lazy="selectin", cascade="all, delete-orphan")
    chat_logs = relationship("ChatLog", back_populates="project", lazy="selectin", cascade="all, delete-orphan")
    memory_items = relationship("MemoryItem", back_populates="project", lazy="select", cascade="all, delete-orphan")
    short_term_entries = relationship("ShortTermMemoryEntry", back_populates="project", lazy="select", cascade="all, delete-orphan")


class AgentSession(Base):
    """Agent execution session tracking."""

    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    plan_id: Mapped[str] = mapped_column(String(100), nullable=True)
    plan_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    phase: Mapped[str] = mapped_column(
        Enum("inception", "blueprinting", "coding", "writing", name="session_phase"),
        default="inception",
    )
    started_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = relationship("Project", back_populates="sessions")


class ChatLog(Base):
    """Chat message log for Agent-User interactions."""

    __tablename__ = "chat_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    sender: Mapped[str] = mapped_column(
        String(50), nullable=False  # "user" / "agent" / "system"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    msg_type: Mapped[str] = mapped_column(
        Enum("thought", "code", "result", "gate", "user_input", name="message_type"),
        default="thought",
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = relationship("Project", back_populates="chat_logs")


class Artifact(Base):
    """Project artifacts (reports, blueprints, code, papers)."""

    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    artifact_type: Mapped[str] = mapped_column(
        Enum("report", "blueprint", "code", "paper", name="artifact_type"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = relationship("Project", back_populates="artifacts")


class MemoryItem(Base):
    """Structured memory item for a single agent step result.

    Implements Layer 3 of the 3-layer context hierarchy:
      Layer 1: Project (Resource)
      Layer 2: Phase (MemoryCategory) — inception/blueprinting/coding/writing
      Layer 3: MemoryItem — individual step results with metadata & keywords

    Inspired by the memU memory framework's MemoryItem model.
    """

    __tablename__ = "memory_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    # Phase this item belongs to (inception/blueprinting/coding/writing)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    # Sequential index within the phase (9999 = synthesis item)
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    # Human-readable step title for display and retrieval
    step_title: Mapped[str] = mapped_column(Text, nullable=False)
    # Full content of the step result
    content: Mapped[str] = mapped_column(Text, default="")
    # Type: "result" | "synthesis" | "analysis" | "code" | "insight"
    content_type: Mapped[str] = mapped_column(String(50), default="result")
    # Extracted keywords for lightweight keyword-based retrieval
    keywords: Mapped[list] = mapped_column(JSONB, default=list)
    # Importance score for retrieval priority:
    #   synthesis=2.0 | user_decision=1.8 | key_finding=1.5 | result=1.0
    importance: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = relationship("Project", back_populates="memory_items")


class ShortTermMemoryEntry(Base):
    """Ephemeral working-memory entry for the current execution session.

    Implements the short-term (session-scoped) tier of the two-tier memory:

      Short-term  — bounded buffer, cleared between phases, fast access
      Long-term   — MemoryItem table, importance-scored, persistent

    A session_id groups entries belonging to one continuous agent run.
    Entries are evicted (oldest first) when the phase capacity is exceeded.
    """

    __tablename__ = "short_term_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    # Identifies the current agent run (UUID string, set per WebSocket session)
    session_id: Mapped[str] = mapped_column(String(100), default="default")
    # Monotonically increasing index within the session for ordering
    sequence_num: Mapped[int] = mapped_column(Integer, default=0)
    # Phase this entry was produced in
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    # Producer role: "agent" | "tool" | "user" | "system"
    role: Mapped[str] = mapped_column(String(20), default="agent")
    # Content classification: "step_result" | "tool_output" | "thought" | "user_message"
    content_type: Mapped[str] = mapped_column(String(50), default="step_result")
    # Full content string
    content: Mapped[str] = mapped_column(Text, default="")
    # Character count for efficient capacity management
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    project = relationship("Project", back_populates="short_term_entries")
