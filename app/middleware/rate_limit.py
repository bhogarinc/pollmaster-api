"""Rate limiting middleware using Redis."""
import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import RateLimitError
from app.core.logging import get_logger

logger = get_logger("pollmaster.middleware.rate_limit")
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis backend."""
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client
        # In-memory fallback if Redis not available
        self._memory_store = {}
    
    def _get_key(self, request: Request) -> str:
        """Generate rate limit key from request."""
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        return f"rate_limit:{client_ip}:{path}"
    
    async def _check_rate_limit(self, key: str) -> tuple[bool, int]:
        """Check if request is within rate limit.
        
        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        now = int(time.time())
        window = settings.RATE_LIMIT_WINDOW
        limit = settings.RATE_LIMIT_REQUESTS
        
        if self.redis:
            # Redis implementation
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            _, current_count, _, _ = await pipe.execute()
            
            if current_count >= limit:
                return False, 0
            return True, limit - current_count - 1
        else:
            # In-memory fallback
            if key not in self._memory_store:
                self._memory_store[key] = []
            
            # Clean old entries
            self._memory_store[key] = [
                t for t in self._memory_store[key] 
                if t > now - window
            ]
            
            current_count = len(self._memory_store[key])
            
            if current_count >= limit:
                return False, 0
            
            self._memory_store[key].append(now)
            return True, limit - current_count - 1
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        key = self._get_key(request)
        allowed, remaining = await self._check_rate_limit(key)
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                ip=request.client.host if request.client else None,
                path=request.url.path
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RateLimitError",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": settings.RATE_LIMIT_WINDOW
                },
                headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW)}
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
