"""
Traffic API - Packet logs (tshark/Stealth capture).
"""

from fastapi import APIRouter, Depends, Query

from scout.infrastructure.database import get_db
from scout.infrastructure.repositories import TrafficRepository
from scout.infrastructure.api.v1.auth import get_current_user
from scout.infrastructure.database import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/traffic", tags=["Traffic"])


@router.get("")
async def list_traffic(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    interface: str | None = Query(None),
    source_ip: str | None = Query(None),
    destination_ip: str | None = Query(None),
):
    """List recent packet logs (from Stealth/tshark captures)."""
    repo = TrafficRepository(db)
    items = await repo.get_recent_traffic(
        limit=limit,
        offset=offset,
        interface=interface,
        source_ip=source_ip,
        destination_ip=destination_ip,
    )
    return {
        "items": [
            {
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                "id": str(p.id),
                "source_ip": str(p.source_ip),
                "destination_ip": str(p.destination_ip),
                "protocol": p.protocol,
                "length": p.length,
                "info": p.info,
                "interface": p.interface,
                "direction": p.direction,
            }
            for p in items
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/aggregates")
async def get_aggregates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    since_minutes: int = Query(60 * 24, ge=1, le=60 * 24 * 7),
    interval_minutes: int = Query(15, ge=1, le=60 * 24),
):
    """Time-series and heatmap (IP x time) aggregates for traffic charts."""
    repo = TrafficRepository(db)
    return await repo.get_aggregates(
        since_minutes=since_minutes,
        interval_minutes=interval_minutes,
    )
