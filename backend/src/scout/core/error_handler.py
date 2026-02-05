"""
Scout Error Handler - Merkezi hata yakalama ve işleme
Decorator ve middleware olarak kullanılabilir
"""

import functools
import traceback
from typing import Callable, Any, TypeVar, Optional
from scout.core.exceptions import ScoutError, AgentError
from scout.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def safe_execute(
    reraise: bool = False,
    default_return: Any = None,
    log_level: str = "error"
):
    """
    Decorator for safe execution with automatic error handling.
    
    Usage:
        @safe_execute(reraise=False, default_return=[])
        async def risky_operation():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except ScoutError as e:
                getattr(logger, log_level)(
                    "Scout error caught",
                    error_code=e.code,
                    error_message=e.message,
                    details=e.details,
                    function=func.__name__
                )
                if reraise:
                    raise
                return default_return
            except Exception as e:
                logger.exception(
                    "Unexpected error caught",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    function=func.__name__,
                    traceback=traceback.format_exc()
                )
                if reraise:
                    raise
                return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except ScoutError as e:
                getattr(logger, log_level)(
                    "Scout error caught",
                    error_code=e.code,
                    error_message=e.message,
                    details=e.details,
                    function=func.__name__
                )
                if reraise:
                    raise
                return default_return
            except Exception as e:
                logger.exception(
                    "Unexpected error caught",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    function=func.__name__,
                    traceback=traceback.format_exc()
                )
                if reraise:
                    raise
                return default_return
        
        # Return appropriate wrapper based on function type
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if function is async"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


class ErrorCollector:
    """
    Collects errors for later reporting/display in UI.
    Singleton pattern for global access.
    """
    _instance: Optional['ErrorCollector'] = None
    _errors: list = []
    _max_errors: int = 1000

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._errors = []
        return cls._instance

    def add_error(self, error: ScoutError, context: Optional[dict] = None):
        """Add an error to the collection"""
        from datetime import datetime
        
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "context": context or {}
        }
        
        self._errors.append(error_entry)
        
        # Keep only last N errors
        if len(self._errors) > self._max_errors:
            self._errors = self._errors[-self._max_errors:]

    def get_errors(self, limit: int = 100, code_filter: Optional[str] = None) -> list:
        """Get recent errors, optionally filtered by code"""
        errors = self._errors[-limit:]
        if code_filter:
            errors = [e for e in errors if e["code"] == code_filter]
        return errors

    def clear(self):
        """Clear all collected errors"""
        self._errors = []


# Global error collector instance
error_collector = ErrorCollector()
