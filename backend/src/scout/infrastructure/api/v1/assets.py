"""
Assets API Endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db, Asset
from scout.infrastructure.repositories import AssetRepository

router = APIRouter(prefix="/assets", tags=["Assets"])


# ============================================
# SCHEMAS
# ============================================
class AssetBase(BaseModel):
    asset_type: str = Field(..., description="Type: ip, hostname, domain, subnet, etc.")
    value: str = Field(..., description="IP address, hostname, or domain")
    label: Optional[str] = Field(None, description="User-friendly name")
    description: Optional[str] = None
    criticality: str = Field("medium", description="low, medium, high, critical")
    environment: str = Field("production", description="production, staging, development")


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    criticality: Optional[str] = None
    environment: Optional[str] = None
    status: Optional[str] = None


class AssetResponse(AssetBase):
    id: UUID
    user_id: UUID
    status: str
    vulnerability_count: int
    risk_score: float
    open_ports: Optional[List[int]] = None
    
    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    skip: int
    limit: int


# ============================================
# ENDPOINTS
# ============================================

# Demo user ID (will be replaced with auth)
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.get("", response_model=AssetListResponse)
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    asset_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all assets for the current user"""
    repo = AssetRepository(db)
    
    if asset_type:
        items = await repo.get_by_type(DEMO_USER_ID, asset_type, skip, limit)
    else:
        items = await repo.get_by_user(DEMO_USER_ID, skip, limit)
    
    total = await repo.count_by_user(DEMO_USER_ID)
    
    return AssetListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/critical", response_model=List[AssetResponse])
async def get_critical_assets(db: AsyncSession = Depends(get_db)):
    """Get high-risk and critical assets"""
    repo = AssetRepository(db)
    return await repo.get_critical_assets(DEMO_USER_ID)


@router.get("/vulnerable", response_model=List[AssetResponse])
async def get_vulnerable_assets(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get assets with known vulnerabilities"""
    repo = AssetRepository(db)
    return await repo.get_vulnerable_assets(DEMO_USER_ID, limit)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific asset by ID"""
    repo = AssetRepository(db)
    asset = await repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("", response_model=AssetResponse, status_code=201)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new asset"""
    repo = AssetRepository(db)
    
    # Check for duplicate
    if data.asset_type == "ip":
        existing = await repo.get_by_ip(DEMO_USER_ID, data.value)
        if existing:
            raise HTTPException(status_code=400, detail="Asset with this IP already exists")
    
    asset = await repo.create(
        user_id=DEMO_USER_ID,
        **data.model_dump()
    )
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an asset"""
    repo = AssetRepository(db)
    
    # Filter out None values
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    asset = await repo.update(asset_id, **update_data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an asset"""
    repo = AssetRepository(db)
    deleted = await repo.delete(asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
