"""
Topology API - Network topology for VectorSpace (nodes, edges, threats).
"""

from uuid import UUID
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db
from scout.infrastructure.api.v1.auth import get_current_user_optional
from scout.infrastructure.database import User
from scout.infrastructure.repositories import (
    AssetRepository,
    TrafficRepository,
    IncidentRepository,
)

router = APIRouter(prefix="/topology", tags=["Topology"])

DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class TopologyNode(BaseModel):
    id: str
    value: str
    label: Optional[str] = None
    asset_type: Optional[str] = None
    status: Optional[str] = None
    risk_score: float = 0.0
    open_ports: Optional[list[int]] = None
    is_scout: bool = False


class TopologyEdge(BaseModel):
    source_ip: str
    destination_ip: str
    packet_count: Optional[int] = None
    last_seen: Optional[str] = None


class TopologyThreat(BaseModel):
    id: str
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None
    severity: str
    title: str


class TopologyResponse(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    threats: list[TopologyThreat]


@router.get("", response_model=TopologyResponse)
async def get_topology(
    since_minutes: int = Query(60 * 24 * 7, ge=1, le=60 * 24 * 30),
    edges_limit: int = Query(500, ge=1, le=2000),
    threats_limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> TopologyResponse:
    """
    Get network topology for VectorSpace: nodes (assets + Scout), edges (from traffic),
    threats (incidents with source/target IP for vector display).
    """
    user_id = current_user.id if current_user else DEMO_USER_ID

    # Nodes: all assets for user + Scout virtual node
    asset_repo = AssetRepository(db)
    items = await asset_repo.get_by_user(user_id, skip=0, limit=1000)
    nodes: list[TopologyNode] = [
        TopologyNode(
            id=str(a.id),
            value=a.value or "",
            label=a.label,
            asset_type=a.asset_type,
            status=a.status,
            risk_score=float(a.risk_score or 0),
            open_ports=a.open_ports,
            is_scout=False,
        )
        for a in items
    ]
    nodes.insert(0, TopologyNode(id="scout", value="scout", label="Scout", is_scout=True))

    # Edges: aggregated connections from packet_logs
    traffic_repo = TrafficRepository(db)
    connections = await traffic_repo.get_connections(since_minutes=since_minutes, limit=edges_limit)
    edges = [
        TopologyEdge(
            source_ip=c["source_ip"],
            destination_ip=c["destination_ip"],
            packet_count=c.get("packet_count"),
            last_seen=c.get("last_seen"),
        )
        for c in connections
    ]

    # Threats: recent incidents with source_ip / target_ip for vector display
    incident_repo = IncidentRepository(db)
    incidents = await incident_repo.get_recent(user_id, hours=since_minutes // 60, limit=threats_limit)
    threats: list[TopologyThreat] = []
    for inc in incidents:
        target_ip: Optional[str] = None
        if inc.target_ip is not None:
            target_ip = str(inc.target_ip)
        threats.append(
            TopologyThreat(
                id=str(inc.id),
                source_ip=str(inc.source_ip) if inc.source_ip else None,
                target_ip=target_ip,
                severity=inc.severity or "medium",
                title=inc.title or "",
            )
        )

    return TopologyResponse(nodes=nodes, edges=edges, threats=threats)
