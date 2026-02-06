"""
Logs API – error logs, audit logs, LLM logs.
"""

from datetime import datetime
from typing import Annotated, List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from scout.core.error_handler import error_collector
from scout.core.logger import get_logger
from scout.infrastructure.database import get_db
from scout.infrastructure.database.models import AuditLog, LlmLog

router = APIRouter(tags=["logs"])
logger = get_logger(__name__)


# --- Audit log schema ---
class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    user_email: Optional[str]
    is_system: bool
    action: str
    action_category: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    description: Optional[str]
    request_path: Optional[str]
    request_method: Optional[str]
    response_status: Optional[int]
    ip_address: Optional[str]
    success: bool
    created_at: str

    class Config:
        from_attributes = True


# --- LLM log schema ---
class LlmLogResponse(BaseModel):
    id: UUID
    provider: str
    model: str
    total_tokens: Optional[int]
    cost_total_usd: Optional[float]
    latency_ms: Optional[int]
    error: bool
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


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


# --- Audit logs (DB) ---
@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[UUID] = Query(None),
    action_category: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """List audit logs with pagination and filters."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
    conditions = []
    if user_id is not None:
        conditions.append(AuditLog.user_id == user_id)
    if action_category is not None:
        conditions.append(AuditLog.action_category == action_category)
    if resource_type is not None:
        conditions.append(AuditLog.resource_type == resource_type)
    if success is not None:
        conditions.append(AuditLog.success == success)
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at >= dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            conditions.append(AuditLog.created_at <= dt)
        except ValueError:
            pass
    if conditions:
        query = select(AuditLog).where(and_(*conditions)).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        AuditLogResponse(
            id=r.id,
            user_id=r.user_id,
            user_email=r.user_email,
            is_system=r.is_system,
            action=r.action,
            action_category=r.action_category,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            description=r.description,
            request_path=r.request_path,
            request_method=r.request_method,
            response_status=r.response_status,
            ip_address=str(r.ip_address) if r.ip_address else None,
            success=r.success,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rows
    ]


# --- LLM logs (DB) ---
@router.get("/llm", response_model=List[LlmLogResponse])
async def get_llm_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    model: Optional[str] = Query(None),
    error: Optional[bool] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """List LLM logs with pagination and filters."""
    query = select(LlmLog).order_by(desc(LlmLog.created_at)).offset(skip).limit(limit)
    conditions = []
    if model is not None:
        conditions.append(LlmLog.model == model)
    if error is not None:
        conditions.append(LlmLog.error == error)
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            conditions.append(LlmLog.created_at >= dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            conditions.append(LlmLog.created_at <= dt)
        except ValueError:
            pass
    if conditions:
        query = select(LlmLog).where(and_(*conditions)).order_by(desc(LlmLog.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        LlmLogResponse(
            id=r.id,
            provider=r.provider,
            model=r.model,
            total_tokens=r.total_tokens,
            cost_total_usd=float(r.cost_total_usd) if r.cost_total_usd is not None else None,
            latency_ms=r.latency_ms,
            error=r.error,
            error_message=r.error_message,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rows
    ]
