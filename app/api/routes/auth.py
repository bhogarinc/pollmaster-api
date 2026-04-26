"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.logging import get_logger

logger = get_logger("pollmaster.api.auth")
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token."""
    # TODO: Implement authentication logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented"
    )


@router.post("/register")
async def register(
    db: AsyncSession = Depends(get_db)
):
    """Register new user account."""
    # TODO: Implement registration logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration not yet implemented"
    )


@router.post("/refresh")
async def refresh_token():
    """Refresh access token."""
    # TODO: Implement token refresh
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented"
    )
