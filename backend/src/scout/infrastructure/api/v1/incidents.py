"""
Incidents API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db, Incident
from scout.infrastructure.repositories import IncidentRepository

router = APIRouter(prefix="/incidents", tags=["Incidents"])


# ============================================
# SCHEMAS
# ============================================
class IncidentBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None
    threat_type: Optional[str] = None
    severity: str = Field("medium", description="info, low, medium, high, critical")
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None


class IncidentCreate(IncidentBase):
    asset_id: Optional[UUID] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None


class IncidentResponse(IncidentBase):
    id: UUID
    user_id: UUID
    incident_number: Optional[str]
    asset_id: Optional[UUID]
    status: str
    priority: str
    detected_at: datetime
    detected_by: Optional[str]
    is_automated: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            # Handle IPv4Address/IPv6Address serialization
            "IPv4Address": str,
            "IPv6Address": str,
        }
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Convert IP addresses to strings before validation
        if hasattr(obj, 'source_ip') and obj.source_ip:
            obj.source_ip = str(obj.source_ip)
        if hasattr(obj, 'target_ip') and obj.target_ip:
            obj.target_ip = str(obj.target_ip)
        return super().model_validate(obj, **kwargs)


class IncidentListResponse(BaseModel):
    items: List[IncidentResponse]
    total: int
    skip: int
    limit: int


class IncidentStatsResponse(BaseModel):
    total: int
    by_status: dict
    by_severity: dict


# ============================================
# ENDPOINTS
# ============================================

DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all incidents"""
    repo = IncidentRepository(db)
    
    if severity:
        items = await repo.get_by_severity(DEMO_USER_ID, severity, skip, limit)
    elif status and status in ["new", "investigating", "contained"]:
        items = await repo.get_open_incidents(DEMO_USER_ID, skip, limit)
    else:
        items = await repo.get_by_user(DEMO_USER_ID, skip, limit)
    
    total = await repo.count_by_user(DEMO_USER_ID)
    
    return IncidentListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/stats", response_model=IncidentStatsResponse)
async def get_incident_stats(db: AsyncSession = Depends(get_db)):
    """Get incident statistics"""
    repo = IncidentRepository(db)
    return await repo.get_stats(DEMO_USER_ID)


@router.get("/recent", response_model=List[IncidentResponse])
async def get_recent_incidents(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get incidents from the last N hours"""
    repo = IncidentRepository(db)
    return await repo.get_recent(DEMO_USER_ID, hours, limit)


@router.get("/open", response_model=List[IncidentResponse])
async def get_open_incidents(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get all open incidents"""
    repo = IncidentRepository(db)
    return await repo.get_open_incidents(DEMO_USER_ID, limit=limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific incident"""
    repo = IncidentRepository(db)
    incident = await repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new incident"""
    repo = IncidentRepository(db)
    incident = await repo.create(
        user_id=DEMO_USER_ID,
        **data.model_dump()
    )
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an incident"""
    repo = IncidentRepository(db)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    incident = await repo.update(incident_id, **update_data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/close", response_model=IncidentResponse)
async def close_incident(
    incident_id: UUID,
    resolution: str = Query(..., description="Resolution type"),
    db: AsyncSession = Depends(get_db)
):
    """Close an incident"""
    repo = IncidentRepository(db)
    incident = await repo.update(
        incident_id,
        status="closed",
        resolution=resolution,
        closed_at=datetime.utcnow()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
