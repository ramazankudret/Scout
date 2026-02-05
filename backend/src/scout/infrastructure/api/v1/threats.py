"""
Threats API Endpoints.

Endpoints for managing security threats.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from scout.domain.entities import Threat, ThreatSeverity, ThreatStatus, ThreatType

router = APIRouter()

# In-memory storage (will be replaced with actual repository)
_threats_db: dict[UUID, Threat] = {}


class CreateThreatRequest(BaseModel):
    """Request body for creating a threat."""

    title: str
    threat_type: ThreatType
    severity: ThreatSeverity = ThreatSeverity.MEDIUM
    description: str | None = None
    source_ip: str | None = None
    target_ip: str | None = None


class UpdateThreatStatusRequest(BaseModel):
    """Request body for updating threat status."""

    status: ThreatStatus
    action: str | None = None


@router.get("")
async def list_threats(
    status: ThreatStatus | None = None,
    severity: ThreatSeverity | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all threats with optional filtering.
    """
    threats = list(_threats_db.values())

    # Apply filters
    if status:
        threats = [t for t in threats if t.status == status]
    if severity:
        threats = [t for t in threats if t.severity == severity]

    # Pagination
    paginated = threats[offset : offset + limit]

    return {
        "total": len(threats),
        "count": len(paginated),
        "offset": offset,
        "limit": limit,
        "threats": [t.model_dump() for t in paginated],
    }


@router.post("")
async def create_threat(request: CreateThreatRequest) -> dict[str, Any]:
    """
    Create a new threat record.
    """
    threat = Threat(
        title=request.title,
        threat_type=request.threat_type,
        severity=request.severity,
        description=request.description,
        source_ip=request.source_ip,
        target_ip=request.target_ip,
    )

    _threats_db[threat.id] = threat

    return {
        "message": "Threat created",
        "threat": threat.model_dump(),
    }


@router.get("/{threat_id}")
async def get_threat(threat_id: UUID) -> dict[str, Any]:
    """
    Get a specific threat by ID.
    """
    threat = _threats_db.get(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    return threat.model_dump()


@router.patch("/{threat_id}/status")
async def update_threat_status(
    threat_id: UUID,
    request: UpdateThreatStatusRequest,
) -> dict[str, Any]:
    """
    Update threat status.
    """
    threat = _threats_db.get(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    if request.status == ThreatStatus.MITIGATED and request.action:
        threat.mitigate(request.action)
    elif request.status == ThreatStatus.FALSE_POSITIVE:
        threat.mark_false_positive(request.action)
    else:
        threat.status = request.status
        threat.update_timestamp()

    return {
        "message": f"Threat status updated to {request.status}",
        "threat": threat.model_dump(),
    }


@router.delete("/{threat_id}")
async def delete_threat(threat_id: UUID) -> dict[str, str]:
    """
    Delete a threat record.
    """
    if threat_id not in _threats_db:
        raise HTTPException(status_code=404, detail="Threat not found")

    del _threats_db[threat_id]

    return {"message": "Threat deleted"}


@router.get("/stats/summary")
async def get_threat_stats() -> dict[str, Any]:
    """
    Get threat statistics summary.
    """
    threats = list(_threats_db.values())

    severity_counts = {}
    status_counts = {}

    for threat in threats:
        severity_counts[threat.severity.value] = severity_counts.get(threat.severity.value, 0) + 1
        status_counts[threat.status.value] = status_counts.get(threat.status.value, 0) + 1

    return {
        "total": len(threats),
        "by_severity": severity_counts,
        "by_status": status_counts,
        "critical_count": severity_counts.get("critical", 0),
        "active_count": status_counts.get("detected", 0) + status_counts.get("confirmed", 0),
    }
