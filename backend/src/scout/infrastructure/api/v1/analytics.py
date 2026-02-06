"""
Analytics API – aggregate data for charts and KPIs.
"""
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db
from scout.infrastructure.database.models import (
    Incident,
    Asset,
    Vulnerability,
    AgentRun,
    SupervisorState,
    AgentExecutionHistory,
    AuditLog,
    LlmLog,
)
from scout.infrastructure.api.v1.auth import get_current_user
from scout.infrastructure.database import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class OverviewResponse(BaseModel):
    incidents_total: int
    incidents_open: int
    assets_total: int
    vulnerabilities_open: int
    agent_runs_total: int
    agent_runs_success: int


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """KPI overview for dashboard."""
    # Incidents total and open
    r = await db.execute(select(func.count()).select_from(Incident))
    incidents_total = r.scalar() or 0
    r = await db.execute(select(func.count()).select_from(Incident).where(Incident.status.in_(["new", "open", "in_progress"])))
    incidents_open = r.scalar() or 0
    # Assets
    r = await db.execute(select(func.count()).select_from(Asset))
    assets_total = r.scalar() or 0
    # Vulnerabilities open
    r = await db.execute(select(func.count()).select_from(Vulnerability).where(Vulnerability.status == "open"))
    vulnerabilities_open = r.scalar() or 0
    # Agent runs
    r = await db.execute(select(func.count()).select_from(AgentRun))
    agent_runs_total = r.scalar() or 0
    r = await db.execute(select(func.count()).select_from(AgentRun).where(AgentRun.status == "completed"))
    agent_runs_success = r.scalar() or 0
    return OverviewResponse(
        incidents_total=incidents_total,
        incidents_open=incidents_open,
        assets_total=assets_total,
        vulnerabilities_open=vulnerabilities_open,
        agent_runs_total=agent_runs_total,
        agent_runs_success=agent_runs_success,
    )


class SeverityCount(BaseModel):
    severity: str
    count: int


@router.get("/incidents-by-severity", response_model=list[SeverityCount])
async def incidents_by_severity(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Incident counts grouped by severity."""
    r = await db.execute(
        select(Incident.severity, func.count(Incident.id).label("count"))
        .group_by(Incident.severity)
    )
    rows = r.all()
    return [SeverityCount(severity=row.severity or "unknown", count=row.count) for row in rows]


class TimeBucket(BaseModel):
    bucket: str
    count: int


@router.get("/incidents-by-time", response_model=list[TimeBucket])
async def incidents_by_time(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    period: str = Query("day", description="day or week"),
):
    """Incident counts over time (detected_at)."""
    if period == "week":
        trunc = func.date_trunc("week", Incident.detected_at)
    else:
        trunc = func.date_trunc("day", Incident.detected_at)
    r = await db.execute(
        select(trunc.label("bucket"), func.count(Incident.id).label("count"))
        .where(Incident.detected_at.isnot(None))
        .group_by(trunc)
        .order_by(trunc)
    )
    rows = r.all()
    return [TimeBucket(bucket=str(row.bucket), count=row.count) for row in rows]


class AgentActivity(BaseModel):
    agent_name: str
    total_executions: int
    success_rate: float


@router.get("/agents-activity", response_model=list[AgentActivity])
async def agents_activity(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Agent activity from supervisor_state (total_executions, success_rate)."""
    r = await db.execute(
        select(
            SupervisorState.agent_name,
            SupervisorState.total_executions,
            SupervisorState.success_rate,
        ).order_by(SupervisorState.agent_name)
    )
    rows = r.all()
    return [
        AgentActivity(
            agent_name=row.agent_name,
            total_executions=row.total_executions or 0,
            success_rate=float(row.success_rate) if row.success_rate is not None else 0.0,
        )
        for row in rows
    ]


class AuditActivityBucket(BaseModel):
    action_category: Optional[str]
    count: int


@router.get("/audit-activity", response_model=list[AuditActivityBucket])
async def audit_activity(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Audit log counts by action_category."""
    r = await db.execute(
        select(AuditLog.action_category, func.count(AuditLog.id).label("count"))
        .group_by(AuditLog.action_category)
    )
    rows = r.all()
    return [AuditActivityBucket(action_category=row.action_category, count=row.count) for row in rows]


class LlmUsageBucket(BaseModel):
    model: str
    total_tokens: int
    total_cost_usd: float
    request_count: int


@router.get("/llm-usage", response_model=list[LlmUsageBucket])
async def llm_usage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """LLM usage aggregated by model."""
    r = await db.execute(
        select(
            LlmLog.model,
            func.coalesce(func.sum(LlmLog.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(LlmLog.cost_total_usd), 0).label("total_cost_usd"),
            func.count(LlmLog.id).label("request_count"),
        ).group_by(LlmLog.model)
    )
    rows = r.all()
    return [
        LlmUsageBucket(
            model=row.model,
            total_tokens=int(row.total_tokens or 0),
            total_cost_usd=float(row.total_cost_usd or 0),
            request_count=row.request_count or 0,
        )
        for row in rows
    ]
