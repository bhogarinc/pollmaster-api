"""Error handling middleware."""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import PollMasterException
from app.core.logging import get_logger

logger = get_logger("pollmaster.middleware.errors")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except PollMasterException as exc:
            # Our custom exceptions
            logger.warning(
                "handled_exception",
                error_type=exc.__class__.__name__,
                message=exc.message,
                path=request.url.path
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.__class__.__name__,
                    "message": exc.message,
                    "details": exc.details
                }
            )
        except Exception as exc:
            # Unhandled exceptions
            logger.exception(
                "unhandled_exception",
                error=str(exc),
                path=request.url.path
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "details": []
                }
            )


# Factory function for middleware
async def error_handler_middleware(request: Request, call_next):
    """ASGI-style error handler middleware."""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("middleware_error", error=str(exc))
        raise
