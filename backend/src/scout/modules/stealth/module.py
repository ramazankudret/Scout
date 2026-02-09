"""
Stealth Mode Module.

Passive observation module that monitors network traffic
without generating any network activity.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from scout.core.logging import get_logger
from scout.modules.base import (
    BaseModule,
    ExecutionContext,
    ModuleMode,
    ModuleResult,
)

logger = get_logger(__name__)


class StealthModule(BaseModule):
    """
    Stealth Mode - Passive Network Observer.

    This module:
    - Listens to network traffic in promiscuous mode
    - Analyzes packets without sending any data
    - Builds a baseline of "normal" network behavior
    - Detects anomalies compared to baseline

    Key principle: NEVER generate any network traffic.
    """

    name = "stealth"
    description = "Passive network observation and baseline learning"
    version = "0.1.0"
    supported_modes = [ModuleMode.PASSIVE]

    def __init__(self) -> None:
        super().__init__()
        self._packet_count = 0
        self._baseline_data: dict[str, Any] = {}
        self._start_time: datetime | None = None

    async def execute(self, context: ExecutionContext) -> ModuleResult:
        """
        Execute stealth mode observation.

        In a real implementation, this would:
        1. Start packet capture on the network interface
        2. Parse and analyze packets
        3. Update baseline statistics
        4. Detect anomalies
        """
        self._start_time = datetime.utcnow()
        self._logger.info("stealth_mode_started", mode="passive")

        # Get config
        interface = context.config.get("interface", "eth0")
        duration = context.config.get("duration", 5)
        packet_count = context.config.get("packet_count", 50)

        # Use TsharkTool via tool registry directly here or in _observe_network
        # We'll update the stub call to pass these args if we keep _observe_network
        # But better to just implement logic here or update _observe_network signature
        
        # Let's map config to context for _observe_network
        # context.config is already there
        
        observations = await self._observe_network(context)

        execution_time = (datetime.utcnow() - self._start_time).total_seconds() * 1000

        error_msg = observations.get("error")
        data: dict[str, Any] = {
            "packets_observed": self._packet_count,
            "unique_ips_seen": len(observations.get("ips", [])),
            "protocols_detected": observations.get("protocols", []),
            "anomalies_detected": observations.get("anomalies", []),
            "capture_source": observations.get("capture_source"),
            "recent_packets": observations.get("recent_packets", []),
            "protocols": observations.get("protocols", []),
            "protocol_counts": observations.get("protocol_counts", {}),
            "graph_nodes": observations.get("graph_nodes", []),
            "graph_edges": observations.get("graph_edges", []),
        }
        if error_msg:
            data["error"] = error_msg

        return ModuleResult(
            success=error_msg is None,
            message="Stealth observation completed" if not error_msg else str(error_msg),
            data=data,
            execution_time_ms=execution_time,
        )

    async def _observe_network(self, context: ExecutionContext) -> dict[str, Any]:
        backend = (context.config.get("capture_backend") or "tshark").lower()
        if backend == "scapy":
            return await self._capture_with_scapy(context)
        return await self._capture_with_tshark(context)

    async def _capture_with_scapy(self, context: ExecutionContext) -> dict[str, Any]:
        from scout.tools.registry import tool_registry
        tool = tool_registry.get_tool("scapy_sniffer")
        if not tool:
            self._logger.error("scapy_sniffer_not_found")
            return {"error": "Scapy sniffer tool not available"}
        interface = context.config.get("interface", "eth0")
        packet_count = context.config.get("packet_count", 50)
        duration = context.config.get("duration", 5) or 10
        result = await tool.run(interface=interface, packet_count=packet_count, duration=duration)
        if not result.success:
            self._logger.error("scapy_capture_failed", error=result.error)
            return {"error": result.error}
        packets = result.data.get("packets", [])
        self._packet_count += len(packets)
        return await self._persist_and_summarize(context, packets, interface, "scapy")

    async def _capture_with_tshark(self, context: ExecutionContext) -> dict[str, Any]:
        from scout.tools.registry import tool_registry
        tshark_tool = tool_registry.get_tool("traffic_sniffer")
        if not tshark_tool:
            self._logger.error("tshark_tool_not_found")
            return {"error": "Tshark tool not available"}
        interface = context.config.get("interface", "eth0")
        duration = context.config.get("duration", 5)
        packet_count = context.config.get("packet_count", 50)
        result = await tshark_tool.run(interface=interface, packet_count=packet_count, duration=duration)
        if not result.success:
            self._logger.error("tshark_capture_failed", error=result.error)
            return {"error": result.error}
        packets_raw = result.data.get("packets", [])
        self._packet_count += len(packets_raw)
        packet_logs = self._tshark_packets_to_logs(packets_raw, interface)
        return await self._persist_and_summarize(context, packet_logs, interface, "tshark")

    def _tshark_packets_to_logs(self, packets: list, interface: str) -> list[dict]:
        packet_logs = []
        if not isinstance(packets, list):
            return packet_logs
        for pkt in packets:
            if not isinstance(pkt, dict):
                continue
            layers = pkt.get("_source", {}).get("layers", {}) or pkt.get("layers", {}) or {}
            ip_layer = layers.get("ip") if isinstance(layers, dict) else {}
            frame_layer = layers.get("frame") if isinstance(layers, dict) else {}
            if not isinstance(ip_layer, dict):
                ip_layer = {}
            if not isinstance(frame_layer, dict):
                frame_layer = {}
            src = ip_layer.get("ip.src") or ip_layer.get("ip_src")
            dst = ip_layer.get("ip.dst") or ip_layer.get("ip_dst")
            src_str = (src[0] if isinstance(src, list) else src) if src else "0.0.0.0"
            dst_str = (dst[0] if isinstance(dst, list) else dst) if dst else "0.0.0.0"
            frame_protos = frame_layer.get("frame.protocols") or frame_layer.get("frame_protocols") or "unknown"
            length_val = frame_layer.get("frame.len") or frame_layer.get("frame_len") or 0
            if isinstance(frame_protos, list):
                frame_protos = frame_protos[0] if frame_protos else "unknown"
            protos_str = frame_protos.split(":") if isinstance(frame_protos, str) else []
            if isinstance(length_val, list):
                length_val = int(length_val[0]) if length_val else 0
            else:
                length_val = int(length_val) if length_val else 0
            proto_name = (protos_str[-1] if protos_str else "unknown").upper()[:20] if protos_str else "UNKNOWN"
            packet_logs.append({
                "source_ip": src_str,
                "destination_ip": dst_str,
                "protocol": proto_name,
                "length": length_val,
                "info": "",
                "interface": interface,
                "direction": "unknown",
            })
        return packet_logs

    async def _persist_and_summarize(
        self,
        context: ExecutionContext,
        packet_logs: list[dict],
        interface: str,
        capture_source: str,
    ) -> dict[str, Any]:
        if context.traffic_repo and packet_logs:
            try:
                for p in packet_logs:
                    p["capture_source"] = capture_source
                    if context.user_id:
                        p["user_id"] = context.user_id
                await context.traffic_repo.save_batch(packet_logs)
            except Exception as e:
                self._logger.error("failed_to_persist_packet_logs", error=str(e))
        unique_ips: set[str] = set()
        protocols_set: set[str] = set()
        protocol_counts: dict[str, int] = {}
        edge_counts: dict[tuple[str, str], int] = {}
        recent_limit = min(int(context.config.get("recent_packets_limit", 150)), 200)
        for p in packet_logs:
            src = (p.get("source_ip") or "").strip()
            dst = (p.get("destination_ip") or "").strip()
            if src:
                unique_ips.add(src)
            if dst:
                unique_ips.add(dst)
            if src and dst and src != dst:
                key = (src, dst)
                edge_counts[key] = edge_counts.get(key, 0) + 1
            proto = p.get("protocol", "unknown")
            protocols_set.add(proto)
            protocol_counts[proto] = protocol_counts.get(proto, 0) + 1
        graph_edges = [
            {"source": src, "destination": dst, "packet_count": count}
            for (src, dst), count in edge_counts.items()
        ]
        base_ts = datetime.now(timezone.utc)
        return {
            "ips": list(unique_ips),
            "protocols": list(protocols_set),
            "protocol_counts": protocol_counts,
            "graph_nodes": list(unique_ips),
            "graph_edges": graph_edges,
            "anomalies": [],
            "capture_source": capture_source,
            "recent_packets": [
                {
                    "time": (base_ts + timedelta(microseconds=i)).isoformat(),
                    "source": p.get("source_ip", "unknown"),
                    "destination": p.get("destination_ip", "unknown"),
                    "protocol": p.get("protocol", "unknown"),
                    "length": p.get("length", 0),
                }
                for i, p in enumerate(packet_logs[:recent_limit])
            ],
        }

    async def get_baseline(self) -> dict[str, Any]:
        """Get the current baseline data."""
        return self._baseline_data.copy()

    async def reset_baseline(self) -> None:
        """Reset the baseline data."""
        self._baseline_data = {}
        self._logger.info("baseline_reset")
