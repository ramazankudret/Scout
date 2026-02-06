"""
TrafficRepository - packet_logs table (tshark/Stealth output).
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database.models import PacketLog
from scout.infrastructure.repositories.base import BaseRepository


class TrafficRepository(BaseRepository[PacketLog]):
    """Repository for packet_logs (traffic capture from tshark/Stealth)."""

    def __init__(self, session: AsyncSession):
        super().__init__(PacketLog, session)

    async def save_packet(
        self,
        source_ip: str,
        destination_ip: str,
        protocol: str,
        length: int,
        info: Optional[str] = None,
        interface: str = "unknown",
        direction: str = "unknown",
    ) -> PacketLog:
        """Save a single packet log."""
        return await self.create(
            source_ip=source_ip,
            destination_ip=destination_ip,
            protocol=protocol,
            length=length,
            info=info or "",
            interface=interface,
            direction=direction,
        )

    async def save_batch(self, packets: List[dict]) -> int:
        """Save a batch of packet log dicts. Each dict has source_ip, destination_ip, protocol, length, info?, interface?."""
        if not packets:
            return 0
        base_ts = datetime.now(timezone.utc)
        for i, p in enumerate(packets):
            # Use microsecond offset so timestamp PK is unique when inserting many rows at once
            ts = base_ts + timedelta(microseconds=i)
            log = PacketLog(
                timestamp=ts,
                source_ip=p.get("source_ip", "0.0.0.0"),
                destination_ip=p.get("destination_ip", "0.0.0.0"),
                protocol=p.get("protocol", "unknown"),
                length=int(p.get("length", 0)),
                info=p.get("info"),
                interface=p.get("interface", "unknown"),
                direction=p.get("direction", "unknown"),
            )
            self.session.add(log)
        await self.session.flush()
        return len(packets)

    async def get_recent_traffic(
        self,
        limit: int = 100,
        offset: int = 0,
        interface: Optional[str] = None,
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
    ) -> List[PacketLog]:
        """Get most recent packet logs with optional filters."""
        query = select(PacketLog)
        if interface:
            query = query.where(PacketLog.interface == interface)
        if source_ip:
            query = query.where(PacketLog.source_ip == source_ip)
        if destination_ip:
            query = query.where(PacketLog.destination_ip == destination_ip)
        query = query.order_by(desc(PacketLog.timestamp)).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
