"""User and Vote database models."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.poll import Poll


class User(Base):
    """Application user account."""
    
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Profile
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_anonymous: Mapped[bool] = mapped_column(default=False)
    
    # OAuth
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50))
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    polls: Mapped[List["Poll"]] = relationship("Poll", back_populates="creator")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Vote(Base):
    """Individual vote record with deduplication support."""
    
    __tablename__ = "votes"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # References
    poll_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("polls.id"), nullable=False
    )
    option_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("poll_options.id"), nullable=False
    )
    
    # Voter identification (anonymous or authenticated)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    voter_identifier: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # Hashed IP + User-Agent or user_id
    
    # Metadata
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 max
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Relationships
    poll: Mapped["Poll"] = relationship("Poll", back_populates="votes")
    option: Mapped["PollOption"] = relationship("PollOption", back_populates="votes")
    
    __table_args__ = (
        # Prevent duplicate votes from same identifier on same poll
        UniqueConstraint("poll_id", "voter_identifier", name="unique_vote_per_voter"),
    )
