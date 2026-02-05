"""
Approval API Endpoints.

REST endpoints for managing action approvals in the HITL system.
"""

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from scout.core.logging import get_logger
from scout.infrastructure.database import get_db
from scout.infrastructure.database.models_approval import PendingAction, ActionApprovalConfig
from scout.infrastructure.repositories.approval_repositories import (
    PendingActionRepository,
    ApprovalPolicyRepository,
)
from scout.infrastructure.api.v1.auth import get_current_user
from scout.infrastructure.database.models import User
from scout.application.services.approval_service import ActionApprovalService
from scout.infrastructure.websocket import websocket_manager

logger = get_logger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────


class PendingActionResponse(BaseModel):
    """Response model for pending actions."""

    id: str
    action_type: str
    module_name: str
    severity: str
    target: str
    target_type: str
    reason: str
    status: str
    confidence_score: float
    created_at: str
    expires_at: str | None
    auto_action: str
    threat_id: str | None = None
    incident_id: str | None = None
    decided_at: str | None = None
    decided_by: str | None = None
    decision_method: str | None = None

    class Config:
        from_attributes = True


class RejectActionRequest(BaseModel):
    """Request to reject an action."""

    reason: str | None = Field(None, max_length=500)


class ApprovalStatsResponse(BaseModel):
    """Response model for approval statistics."""

    pending: int
    approved: int
    rejected: int
    expired: int
    completed: int
    failed: int
    total: int


class ApprovalConfigRequest(BaseModel):
    """Request to create/update approval config."""

    name: str = Field(..., max_length=200)
    description: str | None = None
    action_type: str = Field(..., max_length=50)
    requirement: str = Field("always", pattern="^(always|never|conditional)$")
    conditions: dict = Field(default_factory=dict)
    timeout_seconds: int = Field(300, ge=30, le=3600)
    timeout_action: str = Field("reject", pattern="^(approve|reject)$")
    severity_timeouts: dict = Field(default_factory=dict)
    notify_websocket: bool = True
    notify_email: bool = False
    notify_slack: bool = False
    is_active: bool = True
    priority: int = Field(100, ge=1, le=1000)


class ApprovalConfigResponse(BaseModel):
    """Response model for approval config."""

    id: str
    name: str
    description: str | None
    action_type: str
    requirement: str
    conditions: dict
    timeout_seconds: int
    timeout_action: str
    severity_timeouts: dict
    notify_websocket: bool
    notify_email: bool
    notify_slack: bool
    is_active: bool
    priority: int
    created_at: str
    updated_at: str | None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def _pending_action_to_response(action: PendingAction) -> PendingActionResponse:
    """Convert PendingAction model to response."""
    return PendingActionResponse(
        id=str(action.id),
        action_type=action.action_type,
        module_name=action.module_name,
        severity=action.severity,
        target=action.target,
        target_type=action.target_type,
        reason=action.reason,
        status=action.status,
        confidence_score=float(action.confidence_score),
        created_at=action.created_at.isoformat() if action.created_at else "",
        expires_at=action.expires_at.isoformat() if action.expires_at else None,
        auto_action=action.auto_action,
        threat_id=str(action.threat_id) if action.threat_id else None,
        incident_id=str(action.incident_id) if action.incident_id else None,
        decided_at=action.decided_at.isoformat() if action.decided_at else None,
        decided_by=str(action.decided_by) if action.decided_by else None,
        decision_method=action.decision_method,
    )


def _config_to_response(config: ActionApprovalConfig) -> ApprovalConfigResponse:
    """Convert ActionApprovalConfig model to response."""
    return ApprovalConfigResponse(
        id=str(config.id),
        name=config.name,
        description=config.description,
        action_type=config.action_type,
        requirement=config.requirement,
        conditions=config.conditions or {},
        timeout_seconds=config.timeout_seconds,
        timeout_action=config.timeout_action,
        severity_timeouts=config.severity_timeouts or {},
        notify_websocket=config.notify_websocket,
        notify_email=config.notify_email,
        notify_slack=config.notify_slack,
        is_active=config.is_active,
        priority=config.priority,
        created_at=config.created_at.isoformat() if config.created_at else "",
        updated_at=config.updated_at.isoformat() if config.updated_at else None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pending Actions Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/pending", response_model=List[PendingActionResponse])
async def list_pending_actions(
    status: str | None = Query(None, description="Filter by status"),
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[PendingActionResponse]:
    """
    List pending actions for the current user.

    Supports filtering by status and severity.
    """
    repo = PendingActionRepository(db)
    actions = await repo.get_by_user(
        user_id=current_user.id,
        status=status,
        severity=severity,
        limit=limit,
    )

    return [_pending_action_to_response(a) for a in actions]


@router.get("/pending/stats", response_model=ApprovalStatsResponse)
async def get_approval_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalStatsResponse:
    """Get approval statistics for the current user."""
    repo = PendingActionRepository(db)
    stats = await repo.get_stats(current_user.id)
    return ApprovalStatsResponse(**stats)


@router.get("/pending/{action_id}", response_model=PendingActionResponse)
async def get_pending_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PendingActionResponse:
    """Get details of a specific pending action."""
    repo = PendingActionRepository(db)
    action = await repo.get(action_id)

    if not action:
        raise HTTPException(status_code=404, detail="Pending action not found")

    if action.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this action")

    return _pending_action_to_response(action)


@router.post("/pending/{action_id}/approve")
async def approve_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Approve a pending action.

    The action will be marked for execution.
    """
    repo = PendingActionRepository(db)
    policy_repo = ApprovalPolicyRepository(db)

    service = ActionApprovalService(
        pending_action_repo=repo,
        policy_repo=policy_repo,
        websocket_manager=websocket_manager,
    )

    try:
        action = await service.approve(
            pending_action_id=action_id,
            user_id=current_user.id,
        )
        return {
            "success": True,
            "message": f"Action {action_id} approved",
            "action": _pending_action_to_response(action).model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pending/{action_id}/reject")
async def reject_action(
    action_id: UUID,
    request: RejectActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Reject a pending action.

    The action will not be executed.
    """
    repo = PendingActionRepository(db)
    policy_repo = ApprovalPolicyRepository(db)

    service = ActionApprovalService(
        pending_action_repo=repo,
        policy_repo=policy_repo,
        websocket_manager=websocket_manager,
    )

    try:
        action = await service.reject(
            pending_action_id=action_id,
            user_id=current_user.id,
            reason=request.reason,
        )
        return {
            "success": True,
            "message": f"Action {action_id} rejected",
            "action": _pending_action_to_response(action).model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Approval Configuration Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/config", response_model=List[ApprovalConfigResponse])
async def list_approval_configs(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ApprovalConfigResponse]:
    """List all approval configurations for the current user."""
    repo = ApprovalPolicyRepository(db)
    configs = await repo.get_all_for_user(
        user_id=current_user.id,
        include_inactive=include_inactive,
    )

    return [_config_to_response(c) for c in configs]


@router.post("/config", response_model=ApprovalConfigResponse)
async def create_approval_config(
    request: ApprovalConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalConfigResponse:
    """Create a new approval configuration."""
    repo = ApprovalPolicyRepository(db)

    config = ActionApprovalConfig(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        action_type=request.action_type,
        requirement=request.requirement,
        conditions=request.conditions,
        timeout_seconds=request.timeout_seconds,
        timeout_action=request.timeout_action,
        severity_timeouts=request.severity_timeouts,
        notify_websocket=request.notify_websocket,
        notify_email=request.notify_email,
        notify_slack=request.notify_slack,
        is_active=request.is_active,
        priority=request.priority,
    )

    created = await repo.create(config)
    return _config_to_response(created)


@router.put("/config/{config_id}", response_model=ApprovalConfigResponse)
async def update_approval_config(
    config_id: UUID,
    request: ApprovalConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalConfigResponse:
    """Update an approval configuration."""
    repo = ApprovalPolicyRepository(db)

    config = await repo.get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    if config.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this config")

    # Update fields
    config.name = request.name
    config.description = request.description
    config.action_type = request.action_type
    config.requirement = request.requirement
    config.conditions = request.conditions
    config.timeout_seconds = request.timeout_seconds
    config.timeout_action = request.timeout_action
    config.severity_timeouts = request.severity_timeouts
    config.notify_websocket = request.notify_websocket
    config.notify_email = request.notify_email
    config.notify_slack = request.notify_slack
    config.is_active = request.is_active
    config.priority = request.priority

    updated = await repo.update(config)
    return _config_to_response(updated)


@router.delete("/config/{config_id}")
async def delete_approval_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Delete an approval configuration."""
    repo = ApprovalPolicyRepository(db)

    config = await repo.get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    if config.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this config")

    await repo.delete(config_id)
    return {"message": f"Config {config_id} deleted"}


@router.post("/config/defaults")
async def create_default_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create default approval configurations for the current user."""
    repo = ApprovalPolicyRepository(db)

    # Check if user already has configs
    existing = await repo.get_all_for_user(current_user.id, include_inactive=True)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already has approval configurations"
        )

    configs = await repo.create_default_policies(current_user.id)
    return {
        "message": f"Created {len(configs)} default configurations",
        "configs": [_config_to_response(c).model_dump() for c in configs],
    }
