"""Poll API routes with request validation and auth decorators."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import get_current_user_optional, get_current_user_required, get_db
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.poll import PollStatus, PollVisibility
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.poll import (
    PollCreate, PollDetailResponse, PollListResponse, 
    PollResultsResponse, PollUpdate, VoteRequest
)
from app.services.poll import PollService
from app.services.vote import VoteService

logger = get_logger("pollmaster.api.polls")
router = APIRouter(prefix="/polls", tags=["polls"])
settings = get_settings()


@router.post(
    "",
    response_model=PollDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new poll",
    description="Create a new poll with multiple choice options"
)
async def create_poll(
    request: Request,
    data: PollCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Create a new poll."""
    service = PollService(db)
    
    poll = await service.create_poll(
        creator_id=current_user.id,
        title=data.title,
        options=[opt.model_dump() for opt in data.options],
        description=data.description,
        visibility=data.visibility,
        expires_at=data.expires_at,
        allow_multiple_votes=data.allow_multiple_votes,
        max_votes_per_user=data.max_votes_per_user,
        require_authentication=data.require_authentication,
    )
    
    logger.info(
        "poll_created_via_api",
        poll_id=str(poll.id),
        creator=str(current_user.id),
        ip=request.client.host if request.client else None
    )
    
    return poll


@router.get(
    "",
    response_model=PaginatedResponse[PollListResponse],
    summary="List polls",
    description="List polls with filtering and pagination"
)
async def list_polls(
    request: Request,
    status: Optional[PollStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE, 
        ge=1, 
        le=settings.MAX_PAGE_SIZE,
        description="Items per page"
    ),
    db=Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List polls with filtering."""
    service = PollService(db)
    
    polls, total = await service.list_polls(
        user_id=current_user.id if current_user else None,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse.create(
        items=polls,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/templates",
    response_model=List[PollListResponse],
    summary="Get poll templates",
    description="Get available poll templates"
)
async def get_templates(
    category: Optional[str] = Query(None, description="Template category"),
    db=Depends(get_db)
):
    """Get poll templates."""
    service = PollService(db)
    polls, _ = await service.list_polls(
        is_template=True,
        visibility=PollVisibility.PUBLIC,
        page_size=50
    )
    return polls


@router.get(
    "/{poll_id}",
    response_model=PollDetailResponse,
    summary="Get poll by ID",
    description="Get detailed poll information"
)
async def get_poll(
    poll_id: UUID,
    db=Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get poll details."""
    service = PollService(db)
    user_id = current_user.id if current_user else None
    return await service.get_poll(poll_id, user_id)


@router.get(
    "/by-code/{code}",
    response_model=PollDetailResponse,
    summary="Get poll by code",
    description="Get poll by unique shareable code"
)
async def get_poll_by_code(
    code: str,
    db=Depends(get_db)
):
    """Get poll by shareable code."""
    service = PollService(db)
    return await service.get_poll_by_code(code)


@router.patch(
    "/{poll_id}",
    response_model=PollDetailResponse,
    summary="Update poll",
    description="Update poll settings (creator only)"
)
async def update_poll(
    poll_id: UUID,
    data: PollUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Update poll."""
    service = PollService(db)
    
    updates = data.model_dump(exclude_unset=True)
    poll = await service.update_poll(
        poll_id=poll_id,
        user_id=current_user.id,
        **updates
    )
    
    return poll


@router.post(
    "/{poll_id}/close",
    response_model=PollDetailResponse,
    summary="Close poll",
    description="Manually close a poll (creator only)"
)
async def close_poll(
    poll_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Close poll."""
    service = PollService(db)
    return await service.close_poll(poll_id, current_user.id)


@router.delete(
    "/{poll_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete poll",
    description="Delete a poll (creator only)"
)
async def delete_poll(
    poll_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Delete poll."""
    service = PollService(db)
    await service.delete_poll(poll_id, current_user.id)
    return None


@router.post(
    "/{poll_id}/duplicate",
    response_model=PollDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate poll",
    description="Create a copy of an existing poll"
)
async def duplicate_poll(
    poll_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Duplicate poll."""
    service = PollService(db)
    return await service.duplicate_poll(poll_id, current_user.id)


@router.get(
    "/{poll_id}/results",
    response_model=PollResultsResponse,
    summary="Get poll results",
    description="Get poll results with vote counts and percentages"
)
async def get_results(
    poll_id: UUID,
    db=Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get poll results."""
    # First verify access
    poll_service = PollService(db)
    user_id = current_user.id if current_user else None
    poll = await poll_service.get_poll(poll_id, user_id)
    
    # Get results
    vote_service = VoteService(db)
    return await vote_service.get_results(poll_id)


@router.post(
    "/{poll_id}/vote",
    response_model=PollResultsResponse,
    summary="Cast vote",
    description="Submit a vote for poll options"
)
async def cast_vote(
    request: Request,
    poll_id: UUID,
    data: VoteRequest,
    db=Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Cast vote on poll."""
    vote_service = VoteService(db)
    
    # Generate voter identifier
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    result = await vote_service.cast_vote(
        poll_id=poll_id,
        option_ids=data.option_ids,
        user_id=current_user.id if current_user else None,
        ip_address=ip,
        user_agent=user_agent
    )
    
    logger.info(
        "vote_cast",
        poll_id=str(poll_id),
        voter=str(current_user.id) if current_user else "anonymous",
        options=[str(oid) for oid in data.option_ids]
    )
    
    return result
