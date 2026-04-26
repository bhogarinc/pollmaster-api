"""User management routes."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_required
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger("pollmaster.api.users")
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_required)
):
    """Get current user profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url
    }


@router.get("/{user_id}/polls")
async def get_user_polls(
    user_id: str,
    current_user: User = Depends(get_current_user_required)
):
    """Get polls created by user."""
    # TODO: Implement user polls listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User polls listing not yet implemented"
    )
