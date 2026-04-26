"""Pydantic schemas for poll API."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.poll import PollStatus, PollVisibility


class PollOptionCreate(BaseModel):
    """Schema for creating poll option."""
    text: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    image_url: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class PollOptionResponse(BaseModel):
    """Schema for poll option response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    text: str
    description: Optional[str]
    position: int
    image_url: Optional[str]
    color: Optional[str]
    vote_count: int = 0
    percentage: float = 0.0


class PollCreate(BaseModel):
    """Schema for creating a poll."""
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    options: List[PollOptionCreate] = Field(..., min_length=2, max_length=20)
    visibility: PollVisibility = PollVisibility.PUBLIC
    expires_at: Optional[datetime] = None
    allow_multiple_votes: bool = False
    max_votes_per_user: int = Field(1, ge=1, le=20)
    require_authentication: bool = False
    show_results_before_voting: bool = False
    allow_comments: bool = True
    
    @field_validator("options")
    @classmethod
    def validate_unique_options(cls, v: List[PollOptionCreate]) -> List[PollOptionCreate]:
        texts = [opt.text.strip().lower() for opt in v]
        if len(texts) != len(set(texts)):
            raise ValueError("Duplicate option texts are not allowed")
        return v


class PollUpdate(BaseModel):
    """Schema for updating a poll."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    visibility: Optional[PollVisibility] = None
    expires_at: Optional[datetime] = None
    allow_multiple_votes: Optional[bool] = None
    max_votes_per_user: Optional[int] = Field(None, ge=1, le=20)
    show_results_before_voting: Optional[bool] = None
    allow_comments: Optional[bool] = None


class PollListResponse(BaseModel):
    """Schema for poll list item."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    title: str
    description: Optional[str]
    status: PollStatus
    visibility: PollVisibility
    created_at: datetime
    expires_at: Optional[datetime]
    total_votes: int
    voter_count: int
    is_template: bool
    template_category: Optional[str]


class PollDetailResponse(BaseModel):
    """Schema for detailed poll response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    title: str
    description: Optional[str]
    status: PollStatus
    visibility: PollVisibility
    created_at: datetime
    updated_at: datetime
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    # Settings
    allow_multiple_votes: bool
    max_votes_per_user: int
    allow_comments: bool
    show_results_before_voting: bool
    show_results_after_expiry: bool
    require_authentication: bool
    
    # Stats
    total_votes: int
    voter_count: int
    
    # Template info
    is_template: bool
    template_category: Optional[str]
    duplicated_from_id: Optional[UUID]
    
    # Relationships
    options: List[PollOptionResponse]
    creator: "UserBriefResponse"


class PollResultsOption(BaseModel):
    """Schema for poll results option."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    text: str
    vote_count: int
    percentage: float


class PollResultsResponse(BaseModel):
    """Schema for poll results."""
    poll_id: UUID
    title: str
    status: PollStatus
    total_votes: int
    voter_count: int
    is_expired: bool
    options: List[PollResultsOption]


class VoteRequest(BaseModel):
    """Schema for vote submission."""
    option_ids: List[UUID] = Field(..., min_length=1)
    
    @field_validator("option_ids")
    @classmethod
    def validate_unique_options(cls, v: List[UUID]) -> List[UUID]:
        if len(v) != len(set(v)):
            raise ValueError("Duplicate option votes are not allowed")
        return v


class UserBriefResponse(BaseModel):
    """Brief user info for embedding."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    display_name: str
    avatar_url: Optional[str]


# Update forward references
PollDetailResponse.model_rebuild()
