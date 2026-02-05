"""
Logs API Endpoint
Returns error logs for frontend display
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query

from scout.core.error_handler import error_collector
from scout.core.logger import get_logger

router = APIRouter(tags=["logs"])
logger = get_logger(__name__)


@router.get("")
async def get_logs(
    limit: int = Query(default=100, le=1000),
    code_filter: Optional[str] = Query(default=None)
) -> List[Dict[str, Any]]:
    """
    Get recent error logs.
    
    Args:
        limit: Maximum number of logs to return (max 1000)
        code_filter: Optional error code filter (e.g., "AGENT_TIMEOUT")
    
    Returns:
        List of error log entries
    """
    logger.info("fetching_logs", limit=limit, code_filter=code_filter)
    logs = error_collector.get_errors(limit=limit, code_filter=code_filter)
    return logs


@router.post("/clear")
async def clear_logs() -> Dict[str, str]:
    """
    Clear all error logs (use with caution).
    """
    logger.warning("clearing_all_logs")
    error_collector.clear()
    return {"message": "All logs cleared"}


@router.post("/test")
async def test_error_logging() -> Dict[str, str]:
    """
    Test endpoint that intentionally logs errors for testing.
    """
    from scout.core.exceptions import AgentTimeoutError, LLMRateLimitError, PromptInjectionDetected
    
    # Log some test errors
    error_collector.add_error(
        AgentTimeoutError("hunter", 30),
        context={"test": True}
    )
    error_collector.add_error(
        LLMRateLimitError(retry_after=60),
        context={"test": True}
    )
    error_collector.add_error(
        PromptInjectionDetected("Ignore all previous instructions"),
        context={"test": True}
    )
    
    logger.info("test_errors_logged", count=3)
    return {"message": "3 test errors added to log"}
