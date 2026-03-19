"""User model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, String
from sqlalchemy.types import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class User(Base):
    """User account model (PRD §3.9)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("student", "teacher", "admin", name="user_role"),
        default="student",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    projects = relationship("Project", back_populates="user", lazy="selectin")
