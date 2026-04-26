"""Poll database models with relationships and validators."""
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vote import Vote


class PollStatus(str, PyEnum):
    """Poll lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class PollVisibility(str, PyEnum):
    """Poll visibility options."""
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class Poll(Base):
    """Poll entity with questions, options, and metadata."""
    
    __tablename__ = "polls"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Ownership
    creator_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    
    # Status & Visibility
    status: Mapped[PollStatus] = mapped_column(
        Enum(PollStatus), default=PollStatus.DRAFT, nullable=False
    )
    visibility: Mapped[PollVisibility] = mapped_column(
        Enum(PollVisibility), default=PollVisibility.PUBLIC, nullable=False
    )
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Settings
    allow_multiple_votes: Mapped[bool] = mapped_column(Boolean, default=False)
    max_votes_per_user: Mapped[int] = mapped_column(Integer, default=1)
    allow_comments: Mapped[bool] = mapped_column(Boolean, default=True)
    show_results_before_voting: Mapped[bool] = mapped_column(Boolean, default=False)
    show_results_after_expiry: Mapped[bool] = mapped_column(Boolean, default=True)
    require_authentication: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Template info
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    template_category: Mapped[Optional[str]] = mapped_column(String(50))
    duplicated_from_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("polls.id"), nullable=True
    )
    
    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="polls")
    options: Mapped[List["PollOption"]] = relationship(
        "PollOption", back_populates="poll", cascade="all, delete-orphan"
    )
    votes: Mapped[List["Vote"]] = relationship(
        "Vote", back_populates="poll", cascade="all, delete-orphan"
    )
    duplicated_from: Mapped[Optional["Poll"]] = relationship(
        "Poll", remote_side=[id], backref="duplicates"
    )
    
    @validates("code")
    def validate_code(self, key: str, code: str) -> str:
        if not code or len(code) < 6:
            raise ValueError("Poll code must be at least 6 characters")
        return code.upper()
    
    @validates("title")
    def validate_title(self, key: str, title: str) -> str:
        if not title or len(title.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")
        return title.strip()
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now(self.expires_at.tzinfo) > self.expires_at
        return False
    
    @property
    def total_votes(self) -> int:
        return sum(opt.vote_count for opt in self.options)
    
    @property
    def voter_count(self) -> int:
        return len(set(v.voter_identifier for v in self.votes))


class PollOption(Base):
    """Individual poll option/choice."""
    
    __tablename__ = "poll_options"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    poll_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("polls.id"), nullable=False
    )
    
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    
    # Media
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color
    
    # Vote tracking
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    poll: Mapped["Poll"] = relationship("Poll", back_populates="options")
    votes: Mapped[List["Vote"]] = relationship(
        "Vote", back_populates="option", cascade="all, delete-orphan"
    )
    
    @validates("text")
    def validate_text(self, key: str, text: str) -> str:
        if not text or len(text.strip()) < 1:
            raise ValueError("Option text is required")
        return text.strip()
    
    @property
    def percentage(self) -> float:
        total = self.poll.total_votes if self.poll else 0
        if total == 0:
            return 0.0
        return round((self.vote_count / total) * 100, 2)
