"""API dependencies for authentication and database."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User

logger = get_logger("pollmaster.api.deps")
settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, else None."""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if user and not user.is_active:
            return None
            
        return user
        
    except (JWTError, ValueError) as e:
        logger.debug("jwt_decode_failed", error=str(e))
        return None


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user, raise 401 if not authenticated."""
    user = await get_current_user_optional(credentials, db)
    if user is None:
        raise UnauthorizedError("Invalid or missing authentication token")
    return user


async def get_optional_user_identifier(
    request,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> str:
    """Generate unique voter identifier from user or request fingerprint."""
    if current_user:
        return f"user:{current_user.id}"
    
    # Anonymous voter: hash IP + User-Agent
    import hashlib
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    fingerprint = f"{ip}:{user_agent}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
