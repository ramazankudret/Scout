"""
FastAPI Error Handling Middleware
Global exception handler for all Scout errors
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from scout.core.exceptions import ScoutError
from scout.core.logger import get_logger
from scout.core.error_handler import error_collector

logger = get_logger(__name__)


async def scout_exception_handler(request: Request, exc: ScoutError) -> JSONResponse:
    """
    Handle Scout-specific exceptions and convert to JSON responses.
    """
    logger.error(
        "scout_error",
        error_code=exc.code,
        message=exc.message,
        details=exc.details,
        path=request.url.path
    )
    
    # Add to error collector for UI display
    error_collector.add_error(exc, context={"path": str(request.url.path)})
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.to_dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    """
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle standard HTTP exceptions.
    """
    logger.warning(
        "http_error",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {}
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    """
    logger.exception(
        "unexpected_error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Our team has been notified.",
            "details": {"type": type(exc).__name__}
        }
    )
