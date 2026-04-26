"""Vote service with business logic and deduplication."""
import hashlib
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import (
    ConflictError, ForbiddenError, NotFoundError, ValidationError
)
from app.core.logging import get_logger
from app.models.poll import Poll, PollOption, PollStatus
from app.models.user import User, Vote
from app.repositories.poll import PollRepository

logger = get_logger("pollmaster.services.vote")
settings = get_settings()


class VoteService:
    """Service layer for vote operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.poll_repo = PollRepository(session)
    
    def _generate_voter_identifier(
        self,
        poll_id: UUID,
        user_id: Optional[UUID],
        ip_address: str,
        user_agent: str
    ) -> str:
        """Generate unique voter identifier."""
        if user_id:
            return f"user:{user_id}:{poll_id}"
        
        # Anonymous: hash IP + User-Agent + Poll ID
        fingerprint = f"{ip_address}:{user_agent}:{poll_id}"
        hash_value = hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
        return f"anon:{hash_value}"
    
    async def _validate_vote(
        self,
        poll: Poll,
        option_ids: List[UUID],
        user_id: Optional[UUID],
        voter_id: str
    ) -> None:
        """Validate vote request."""
        errors = []
        
        # Check poll status
        if poll.status != PollStatus.ACTIVE:
            errors.append(f"Poll is {poll.status.value}")
        
        if poll.is_expired:
            errors.append("Poll has expired")
        
        # Check authentication requirement
        if poll.require_authentication and not user_id:
            raise ForbiddenError("Authentication required to vote")
        
        # Check multiple votes
        if not poll.allow_multiple_votes and len(option_ids) > 1:
            errors.append("Multiple votes not allowed for this poll")
        
        if len(option_ids) > poll.max_votes_per_user:
            errors.append(
                f"Maximum {poll.max_votes_per_user} vote(s) allowed"
            )
        
        # Validate options belong to poll
        poll_option_ids = {opt.id for opt in poll.options}
        invalid_options = set(option_ids) - poll_option_ids
        if invalid_options:
            errors.append(f"Invalid option(s): {invalid_options}")
        
        # Check for duplicate vote
        existing = await self.session.execute(
            select(Vote).where(
                Vote.poll_id == poll.id,
                Vote.voter_identifier == voter_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("You have already voted in this poll")
        
        if errors:
            raise ValidationError("Vote validation failed", details=errors)
    
    async def cast_vote(
        self,
        poll_id: UUID,
        option_ids: List[UUID],
        user_id: Optional[UUID] = None,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> dict:
        """Cast vote on poll."""
        # Get poll with options
        poll = await self.poll_repo.get_by_id(poll_id, load_options=True)
        if not poll:
            raise NotFoundError(f"Poll {poll_id} not found")
        
        # Generate voter identifier
        voter_id = self._generate_voter_identifier(
            poll_id, user_id, ip_address, user_agent
        )
        
        # Validate vote
        await self._validate_vote(poll, option_ids, user_id, voter_id)
        
        # Create vote records
        votes = []
        for option_id in option_ids:
            vote = Vote(
                poll_id=poll_id,
                option_id=option_id,
                user_id=user_id,
                voter_identifier=voter_id,
                ip_address=ip_address[:45] if ip_address else None,
                user_agent=user_agent[:500] if user_agent else None
            )
            self.session.add(vote)
            votes.append(vote)
            
            # Update option vote count
            option = next(
                (opt for opt in poll.options if opt.id == option_id), None
            )
            if option:
                option.vote_count += 1
        
        await self.session.commit()
        
        logger.info(
            "vote_cast",
            poll_id=str(poll_id),
            voter_id=voter_id[:16],
            options_count=len(option_ids)
        )
        
        # Return updated results
        return await self.get_results(poll_id)
    
    async def get_results(self, poll_id: UUID) -> dict:
        """Get poll results with vote counts."""
        poll = await self.poll_repo.get_by_id(poll_id, load_options=True)
        if not poll:
            raise NotFoundError(f"Poll {poll_id} not found")
        
        total_votes = sum(opt.vote_count for opt in poll.options)
        
        options_results = []
        for opt in poll.options:
            percentage = (
                round((opt.vote_count / total_votes) * 100, 2)
                if total_votes > 0 else 0.0
            )
            options_results.append({
                "id": opt.id,
                "text": opt.text,
                "vote_count": opt.vote_count,
                "percentage": percentage
            })
        
        # Get unique voter count
        voter_count_result = await self.session.execute(
            select(func.count(func.distinct(Vote.voter_identifier)))
            .where(Vote.poll_id == poll_id)
        )
        voter_count = voter_count_result.scalar() or 0
        
        return {
            "poll_id": poll.id,
            "title": poll.title,
            "status": poll.status.value,
            "total_votes": total_votes,
            "voter_count": voter_count,
            "is_expired": poll.is_expired,
            "options": options_results
        }
    
    async def has_voted(
        self,
        poll_id: UUID,
        user_id: Optional[UUID] = None,
        ip_address: str = "",
        user_agent: str = ""
    ) -> bool:
        """Check if user has already voted."""
        voter_id = self._generate_voter_identifier(
            poll_id, user_id, ip_address, user_agent
        )
        
        result = await self.session.execute(
            select(Vote).where(
                Vote.poll_id == poll_id,
                Vote.voter_identifier == voter_id
            )
        )
        return result.scalar_one_or_none() is not None
