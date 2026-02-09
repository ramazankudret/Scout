"""
Discovery API - Subnet discovery (Nmap -sn / Netdiscover) without full Hunter run.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db
from scout.infrastructure.api.v1.auth import get_current_user_optional
from scout.infrastructure.database import User
from scout.infrastructure.repositories import AssetRepository
from scout.modules import ExecutionContext, ModuleMode, module_registry

router = APIRouter(prefix="/discovery", tags=["Discovery"])

DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class DiscoveryScanRequest(BaseModel):
    subnet: str  # e.g. 192.168.1.0/24


class DiscoveryScanResponse(BaseModel):
    subnet: str
    discovered_count: int
    discovered_ips: list[str]
    scanner_used: str


@router.post("/scan", response_model=DiscoveryScanResponse)
async def discovery_scan(
    body: DiscoveryScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> DiscoveryScanResponse:
    """
    Run subnet discovery only: Nmap -sn or Netdiscover, create assets for each discovered IP.
    """
    from scout.modules.hunter.module import HunterModule, _is_cidr

    if not _is_cidr(body.subnet):
        raise HTTPException(
            status_code=400,
            detail="Invalid subnet. Use CIDR format, e.g. 192.168.1.0/24",
        )

    user_id = current_user.id if current_user else DEMO_USER_ID
    context = ExecutionContext(
        mode=ModuleMode.ACTIVE,
        config={},
        asset_repo=AssetRepository(db),
        traffic_repo=None,
        scan_result_repo=None,
        user_id=user_id,
    )

    hunter = module_registry.get("hunter")
    if not isinstance(hunter, HunterModule):
        raise HTTPException(status_code=503, detail="Hunter module not available")

    result = await hunter._discover_subnet(context=context, cidr=body.subnet)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return DiscoveryScanResponse(
        subnet=result["cidr"],
        discovered_count=result["count"],
        discovered_ips=result["discovered_ips"],
        scanner_used=result.get("scanner_used", "nmap"),
    )
