"""Poll repository with CRUD operations, pagination, and filtering."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.poll import Poll, PollOption, PollStatus, PollVisibility

logger = get_logger("pollmaster.repositories.poll")
settings = get_settings()


class PollRepository:
    """Repository for poll data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(
        self, 
        poll_id: UUID, 
        *,
        load_options: bool = True,
        load_votes: bool = False
    ) -> Optional[Poll]:
        """Get poll by ID with optional eager loading."""
        query = select(Poll).where(Poll.id == poll_id)
        
        if load_options:
            query = query.options(selectinload(Poll.options))
        if load_votes:
            query = query.options(selectinload(Poll.votes))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[Poll]:
        """Get poll by unique code."""
        result = await self.session.execute(
            select(Poll)
            .where(Poll.code == code.upper())
            .options(selectinload(Poll.options))
        )
        return result.scalar_one_or_none()
    
    async def list_polls(
        self,
        *,
        creator_id: Optional[UUID] = None,
        status: Optional[PollStatus] = None,
        visibility: Optional[PollVisibility] = None,
        is_template: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = None,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> tuple[List[Poll], int]:
        """List polls with filtering and pagination.
        
        Returns:
            Tuple of (polls list, total count)
        """
        page_size = page_size or settings.DEFAULT_PAGE_SIZE
        
        # Build base query
        query = select(Poll).options(selectinload(Poll.options))
        count_query = select(func.count(Poll.id))
        
        filters = []
        
        if creator_id:
            filters.append(Poll.creator_id == creator_id)
        if status:
            filters.append(Poll.status == status)
        if visibility:
            filters.append(Poll.visibility == visibility)
        if is_template is not None:
            filters.append(Poll.is_template == is_template)
        if search:
            search_filter = or_(
                Poll.title.ilike(f"%{search}%"),
                Poll.description.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Apply ordering
        order_column = getattr(Poll, order_by, Poll.created_at)
        if order_desc:
            order_column = order_column.desc()
        query = query.order_by(order_column)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        polls = result.scalars().all()
        
        logger.debug(
            "polls_listed",
            count=len(polls),
            total=total,
            page=page,
            filters={k: str(v) for k, v in locals().items() if k.endswith('_id') or k in ['status', 'visibility']}
        )
        
        return list(polls), total
    
    async def create(self, poll: Poll) -> Poll:
        """Create new poll."""
        self.session.add(poll)
        await self.session.flush()
        await self.session.refresh(poll)
        logger.info("poll_created", poll_id=str(poll.id), code=poll.code)
        return poll
    
    async def update(self, poll: Poll) -> Poll:
        """Update existing poll."""
        await self.session.flush()
        await self.session.refresh(poll)
        logger.info("poll_updated", poll_id=str(poll.id))
        return poll
    
    async def delete(self, poll: Poll) -> None:
        """Delete poll."""
        await self.session.delete(poll)
        logger.info("poll_deleted", poll_id=str(poll.id))
    
    async def duplicate(self, original_poll: Poll, new_code: str) -> Poll:
        """Duplicate a poll with new code."""
        # Create new poll with copied data
        new_poll = Poll(
            code=new_code,
            title=f"{original_poll.title} (Copy)",
            description=original_poll.description,
            creator_id=original_poll.creator_id,
            status=PollStatus.DRAFT,
            visibility=original_poll.visibility,
            allow_multiple_votes=original_poll.allow_multiple_votes,
            max_votes_per_user=original_poll.max_votes_per_user,
            allow_comments=original_poll.allow_comments,
            show_results_before_voting=original_poll.show_results_before_voting,
            show_results_after_expiry=original_poll.show_results_after_expiry,
            require_authentication=original_poll.require_authentication,
            duplicated_from_id=original_poll.id,
        )
        
        self.session.add(new_poll)
        await self.session.flush()
        
        # Copy options
        for opt in original_poll.options:
            new_option = PollOption(
                poll_id=new_poll.id,
                text=opt.text,
                description=opt.description,
                position=opt.position,
                image_url=opt.image_url,
                color=opt.color,
            )
            self.session.add(new_option)
        
        await self.session.flush()
        await self.session.refresh(new_poll)
        
        logger.info(
            "poll_duplicated",
            original_id=str(original_poll.id),
            new_id=str(new_poll.id),
            new_code=new_code
        )
        
        return new_poll
    
    async def code_exists(self, code: str) -> bool:
        """Check if poll code already exists."""
        result = await self.session.execute(
            select(func.count(Poll.id)).where(Poll.code == code.upper())
        )
        return result.scalar() > 0
