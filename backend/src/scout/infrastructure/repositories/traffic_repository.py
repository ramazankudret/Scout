"""
TrafficRepository - packet_logs table (tshark/Stealth output).
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any

from sqlalchemy import select, desc, func, text
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
                capture_source=p.get("capture_source"),
                user_id=p.get("user_id"),
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

    async def get_connections(
        self,
        since_minutes: int = 60 * 24,
        limit: int = 500,
    ) -> List[dict]:
        """
        Aggregate packet_logs into unique source_ip -> destination_ip connections.
        Returns list of { source_ip, destination_ip, packet_count, last_seen }.
        Excludes self-loops (source_ip = destination_ip).
        """
        since = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        packet_count_label = func.count().label("packet_count")
        query = (
            select(
                PacketLog.source_ip,
                PacketLog.destination_ip,
                packet_count_label,
                func.max(PacketLog.timestamp).label("last_seen"),
            )
            .where(PacketLog.timestamp >= since)
            .where(PacketLog.source_ip != PacketLog.destination_ip)
            .group_by(PacketLog.source_ip, PacketLog.destination_ip)
            .order_by(desc(packet_count_label))
            .limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.all()
        return [
            {
                "source_ip": str(r.source_ip),
                "destination_ip": str(r.destination_ip),
                "packet_count": r.packet_count,
                "last_seen": r.last_seen.isoformat() if r.last_seen else None,
            }
            for r in rows
        ]

    async def get_aggregates(
        self,
        since_minutes: int = 60 * 24,
        interval_minutes: int = 15,
    ) -> dict[str, Any]:
        """
        Time-series aggregation for charts: bucket packet_logs by time interval.
        Returns bucket_start (ISO), packet_count, byte_count per bucket.
        Also returns heatmap_data: per (bucket_start, source_ip) packet counts for IP x time heatmap.
        """
        since = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        interval_m = max(1, min(interval_minutes, 60 * 24))
        interval_sec = interval_m * 60
        time_series_sql = text("""
            SELECT
                to_timestamp(floor(extract(epoch from "timestamp") / :interval_sec) * :interval_sec) at time zone 'UTC' AS bucket_start,
                count(*)::int AS packet_count,
                coalesce(sum(length), 0)::bigint AS byte_count
            FROM packet_logs
            WHERE "timestamp" >= :since
            GROUP BY 1
            ORDER BY 1
        """)
        heatmap_sql = text("""
            SELECT
                to_timestamp(floor(extract(epoch from "timestamp") / :interval_sec) * :interval_sec) at time zone 'UTC' AS bucket_start,
                source_ip::text AS ip,
                count(*)::int AS packet_count
            FROM packet_logs
            WHERE "timestamp" >= :since
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC
        """)
        result_ts = await self.session.execute(
            time_series_sql,
            {"interval_sec": interval_sec, "since": since},
        )
        result_hm = await self.session.execute(
            heatmap_sql,
            {"interval_sec": interval_sec, "since": since},
        )
        rows_ts = result_ts.fetchall()
        rows_hm = result_hm.fetchall()
        time_series = [
            {
                "bucket_start": r[0].isoformat() if r[0] else None,
                "packet_count": r[1] or 0,
                "byte_count": r[2] or 0,
            }
            for r in rows_ts
        ]
        heatmap_data = [
            {
                "bucket_start": r[0].isoformat() if r[0] else None,
                "ip": r[1] or "",
                "packet_count": r[2] or 0,
            }
            for r in rows_hm
        ]
        return {
            "since_minutes": since_minutes,
            "interval_minutes": interval_m,
            "time_series": time_series,
            "heatmap_data": heatmap_data,
        }
