"""Custom exception classes for PollMaster."""
from typing import Any, Dict, List, Optional


class PollMasterException(Exception):
    """Base exception for PollMaster."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[List[str]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


class NotFoundError(PollMasterException):
    """Resource not found."""
    
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(message, status_code=404, details=details)


class ValidationError(PollMasterException):
    """Input validation error."""
    
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(message, status_code=422, details=details)


class ConflictError(PollMasterException):
    """Resource conflict."""
    
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(message, status_code=409, details=details)


class ForbiddenError(PollMasterException):
    """Access forbidden."""
    
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(message, status_code=403, details=details)


class UnauthorizedError(PollMasterException):
    """Authentication required."""
    
    def __init__(self, message: str = "Authentication required", details: Optional[List[str]] = None):
        super().__init__(message, status_code=401, details=details)


class RateLimitError(PollMasterException):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
