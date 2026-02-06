"""
Scans API - Scan result history (nmap, masscan, etc.).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from scout.infrastructure.database import get_db
from scout.infrastructure.repositories import ScanResultRepository
from scout.infrastructure.api.v1.auth import get_current_user
from scout.infrastructure.database import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.get("")
async def list_scans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scan_type: str | None = Query(None),
    scanner_used: str | None = Query(None),
    target: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List scan results for the current user with optional filters."""
    repo = ScanResultRepository(db)
    items = await repo.list_by_user(
        user_id=current_user.id,
        scan_type=scan_type,
        scanner_used=scanner_used,
        target=target,
        limit=limit,
        offset=offset,
    )
    total = await repo.count_by_user(
        user_id=current_user.id,
        scan_type=scan_type,
        scanner_used=scanner_used,
        target=target,
    )
    return {
        "items": [
            {
                "id": str(s.id),
                "scan_type": s.scan_type,
                "scanner_used": s.scanner_used,
                "target": s.target,
                "status": s.status,
                "open_ports": s.open_ports or [],
                "open_ports_count": len(s.open_ports) if s.open_ports else 0,
                "services_found": s.services_found or [],
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "duration_seconds": s.duration_seconds,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{scan_id}")
async def get_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single scan result by ID."""
    repo = ScanResultRepository(db)
    scan = await repo.get(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "id": str(scan.id),
        "scan_type": scan.scan_type,
        "scanner_used": scan.scanner_used,
        "target": scan.target,
        "status": scan.status,
        "open_ports": scan.open_ports or [],
        "services_found": scan.services_found or [],
        "parsed_results": scan.parsed_results or {},
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "duration_seconds": scan.duration_seconds,
        "error_message": scan.error_message,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
    }
