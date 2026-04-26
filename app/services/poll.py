"""Poll service with business logic, validation, and error handling."""
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import (
    ConflictError, NotFoundError, ValidationError, ForbiddenError
)
from app.core.logging import get_logger
from app.models.poll import Poll, PollOption, PollStatus, PollVisibility
from app.repositories.poll import PollRepository

logger = get_logger("pollmaster.services.poll")
settings = get_settings()


class PollService:
    """Service layer for poll business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PollRepository(session)
    
    def _generate_code(self, length: int = None) -> str:
        """Generate unique poll code."""
        length = length or settings.POLL_CODE_LENGTH
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def _generate_unique_code(self, retries: int = 10) -> str:
        """Generate unique poll code with retry logic."""
        for attempt in range(retries):
            code = self._generate_code()
            if not await self.repo.code_exists(code):
                return code
        raise ConflictError("Could not generate unique poll code")
    
    def _validate_poll_data(
        self,
        title: str,
        options: List[dict],
        expires_at: Optional[datetime] = None
    ) -> None:
        """Validate poll creation data."""
        errors = []
        
        # Validate title
        if not title or len(title.strip()) < 3:
            errors.append("Title must be at least 3 characters")
        if len(title) > 200:
            errors.append("Title must not exceed 200 characters")
        
        # Validate options
        if len(options) < 2:
            errors.append("At least 2 options are required")
        if len(options) > settings.MAX_OPTIONS_PER_POLL:
            errors.append(f"Maximum {settings.MAX_OPTIONS_PER_POLL} options allowed")
        
        for i, opt in enumerate(options):
            text = opt.get("text", "").strip()
            if not text:
                errors.append(f"Option {i+1} text is required")
            elif len(text) > 500:
                errors.append(f"Option {i+1} text must not exceed 500 characters")
        
        # Validate expiration
        if expires_at:
            max_date = datetime.now(expires_at.tzinfo) + timedelta(
                days=settings.MAX_POLL_DURATION_DAYS
            )
            if expires_at > max_date:
                errors.append(
                    f"Poll cannot exceed {settings.MAX_POLL_DURATION_DAYS} days"
                )
            if expires_at < datetime.now(expires_at.tzinfo):
                errors.append("Expiration date must be in the future")
        
        if errors:
            raise ValidationError("Poll validation failed", details=errors)
    
    async def create_poll(
        self,
        creator_id: UUID,
        title: str,
        options: List[dict],
        description: Optional[str] = None,
        visibility: PollVisibility = PollVisibility.PUBLIC,
        expires_at: Optional[datetime] = None,
        allow_multiple_votes: bool = False,
        max_votes_per_user: int = 1,
        require_authentication: bool = False,
        **kwargs
    ) -> Poll:
        """Create new poll with validation."""
        self._validate_poll_data(title, options, expires_at)
        
        code = await self._generate_unique_code()
        
        poll = Poll(
            code=code,
            title=title.strip(),
            description=description.strip() if description else None,
            creator_id=creator_id,
            status=PollStatus.ACTIVE,
            visibility=visibility,
            expires_at=expires_at,
            allow_multiple_votes=allow_multiple_votes,
            max_votes_per_user=max_votes_per_user,
            require_authentication=require_authentication,
            **kwargs
        )
        
        try:
            created_poll = await self.repo.create(poll)
            
            # Create options
            for i, opt_data in enumerate(options):
                option = PollOption(
                    poll_id=created_poll.id,
                    text=opt_data["text"].strip(),
                    description=opt_data.get("description", "").strip() or None,
                    position=i,
                    image_url=opt_data.get("image_url"),
                    color=opt_data.get("color"),
                )
                self.session.add(option)
            
            await self.session.commit()
            logger.info("poll_created", poll_id=str(created_poll.id), code=code)
            return created_poll
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error("poll_create_failed", error=str(e))
            raise ConflictError("Failed to create poll")
    
    async def get_poll(
        self, 
        poll_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Poll:
        """Get poll by ID with access check."""
        poll = await self.repo.get_by_id(poll_id)
        if not poll:
            raise NotFoundError(f"Poll {poll_id} not found")
        
        # Check visibility
        if poll.visibility == PollVisibility.PRIVATE:
            if not user_id or poll.creator_id != user_id:
                raise ForbiddenError("Access denied to private poll")
        
        return poll
    
    async def get_poll_by_code(self, code: str) -> Poll:
        """Get poll by code."""
        poll = await self.repo.get_by_code(code)
        if not poll:
            raise NotFoundError(f"Poll with code '{code}' not found")
        return poll
    
    async def list_polls(
        self,
        *,
        user_id: Optional[UUID] = None,
        status: Optional[PollStatus] = None,
        visibility: Optional[PollVisibility] = PollVisibility.PUBLIC,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = None
    ) -> Tuple[List[Poll], int]:
        """List polls with filtering."""
        # If user is requesting their own polls, show all
        if user_id:
            return await self.repo.list_polls(
                creator_id=user_id,
                status=status,
                page=page,
                page_size=page_size
            )
        
        # Public listing - only public polls
        return await self.repo.list_polls(
            status=status or PollStatus.ACTIVE,
            visibility=visibility,
            search=search,
            page=page,
            page_size=page_size
        )
    
    async def update_poll(
        self,
        poll_id: UUID,
        user_id: UUID,
        **updates
    ) -> Poll:
        """Update poll with ownership check."""
        poll = await self.get_poll(poll_id, user_id)
        
        if poll.creator_id != user_id:
            raise ForbiddenError("Only poll creator can update")
        
        # Prevent updates to closed polls
        if poll.status == PollStatus.CLOSED:
            raise ForbiddenError("Cannot update closed poll")
        
        # Apply allowed updates
        allowed_fields = [
            "title", "description", "visibility", "expires_at",
            "allow_multiple_votes", "max_votes_per_user",
            "show_results_before_voting", "allow_comments"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(poll, field, value)
        
        updated = await self.repo.update(poll)
        await self.session.commit()
        return updated
    
    async def close_poll(self, poll_id: UUID, user_id: UUID) -> Poll:
        """Close poll manually."""
        poll = await self.get_poll(poll_id, user_id)
        
        if poll.creator_id != user_id:
            raise ForbiddenError("Only poll creator can close")
        
        poll.status = PollStatus.CLOSED
        updated = await self.repo.update(poll)
        await self.session.commit()
        
        logger.info("poll_closed", poll_id=str(poll_id), by=str(user_id))
        return updated
    
    async def delete_poll(self, poll_id: UUID, user_id: UUID) -> None:
        """Delete poll with ownership check."""
        poll = await self.get_poll(poll_id, user_id)
        
        if poll.creator_id != user_id:
            raise ForbiddenError("Only poll creator can delete")
        
        await self.repo.delete(poll)
        await self.session.commit()
        
        logger.info("poll_deleted", poll_id=str(poll_id), by=str(user_id))
    
    async def duplicate_poll(
        self,
        poll_id: UUID,
        user_id: UUID
    ) -> Poll:
        """Duplicate existing poll."""
        original = await self.get_poll(poll_id, user_id)
        
        # Check permissions for private polls
        if original.visibility == PollVisibility.PRIVATE:
            if original.creator_id != user_id:
                raise ForbiddenError("Cannot duplicate private poll")
        
        new_code = await self._generate_unique_code()
        duplicated = await self.repo.duplicate(original, new_code)
        await self.session.commit()
        
        return duplicated
