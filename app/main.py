"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, polls, users, websocket
from app.core.config import get_settings
from app.core.errors import PollMasterException
from app.core.logging import configure_logging, get_logger
from app.db.base import close_db, init_db
from app.middleware.errors import error_handler_middleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

settings = get_settings()
logger = get_logger("pollmaster.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    configure_logging()
    logger.info(
        "application_starting",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )
    await init_db()
    yield
    # Shutdown
    await close_db()
    logger.info("application_shutting_down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time polling and survey REST API platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(error_handler_middleware)

# Exception handlers
@app.exception_handler(PollMasterException)
async def pollmaster_exception_handler(request, exc: PollMasterException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": getattr(request.state, "correlation_id", "")
        }
    )

# Health check
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

# API routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(polls.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")

# Root redirect to docs in debug
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "api": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS
    )
