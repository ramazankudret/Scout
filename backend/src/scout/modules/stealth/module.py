"""
Stealth Mode Module.

Passive observation module that monitors network traffic
without generating any network activity.
"""

from datetime import datetime
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

        return ModuleResult(
            success=True,
            message="Stealth observation completed",
            data={
                "packets_observed": self._packet_count,
                "unique_ips_seen": len(observations.get("ips", [])),
                "protocols_detected": observations.get("protocols", []),
                "anomalies_detected": observations.get("anomalies", []),
            },
            execution_time_ms=execution_time,
        )

    async def _observe_network(self, context: ExecutionContext) -> dict[str, Any]:
        # Use TsharkTool
        from scout.tools.registry import tool_registry
        tshark_tool = tool_registry.get_tool("traffic_sniffer")
        
        if not tshark_tool:
            self._logger.error("tshark_tool_not_found")
            return {"error": "Tshark tool not available"}

        interface = context.config.get("interface", "eth0")
        duration = context.config.get("duration", 5)
        packet_count = context.config.get("packet_count", 50)

        # Perform capture
        result = await tshark_tool.run(interface=interface, packet_count=packet_count, duration=duration)
        
        if not result.success:
            self._logger.error("tshark_capture_failed", error=result.error)
            return {"error": result.error}

        packets = result.data.get("packets", [])
        self._packet_count += len(packets)

        unique_ips = set()
        protocols = set()
        packet_logs: list[dict] = []

        for pkt in packets:
            layers = pkt.get("_source", {}).get("layers", {}) or {}
            ip_layer = layers.get("ip")
            frame_layer = layers.get("frame")
            src = None
            dst = None
            if isinstance(ip_layer, dict):
                src = ip_layer.get("ip.src")
                dst = ip_layer.get("ip.dst")
            if src is not None:
                unique_ips.add(src[0] if isinstance(src, list) else src)
            if dst is not None:
                unique_ips.add(dst[0] if isinstance(dst, list) else dst)
            src_str = (src[0] if isinstance(src, list) else src) if src is not None else "0.0.0.0"
            dst_str = (dst[0] if isinstance(dst, list) else dst) if dst is not None else "0.0.0.0"
            frame_protos = "unknown"
            length_val = 0
            if isinstance(frame_layer, dict):
                frame_protos = frame_layer.get("frame.protocols", "unknown") or "unknown"
                length_val = frame_layer.get("frame.len", 0) or 0
            if isinstance(frame_protos, list):
                frame_protos = frame_protos[0] if frame_protos else "unknown"
            protos_str = frame_protos.split(":") if isinstance(frame_protos, str) else []
            protocols.update(protos_str)
            if isinstance(length_val, list):
                length_val = int(length_val[0]) if length_val else 0
            else:
                length_val = int(length_val) if length_val else 0
            proto_name = (protos_str[-1] if protos_str else "unknown").upper()[:20]
            packet_logs.append({
                "source_ip": src_str,
                "destination_ip": dst_str,
                "protocol": proto_name,
                "length": length_val,
                "info": "",
                "interface": interface,
                "direction": "unknown",
            })

        if context.traffic_repo and packet_logs:
            try:
                await context.traffic_repo.save_batch(packet_logs)
            except Exception as e:
                self._logger.error("failed_to_persist_packet_logs", error=str(e))

        return {
            "ips": list(unique_ips),
            "protocols": list(protocols),
            "anomalies": [],
            "recent_packets": [
                {
                    "time": datetime.utcnow().isoformat(),
                    "source": pkt.get("_source", {}).get("layers", {}).get("ip", {}).get("ip.src", "unknown"),
                    "destination": pkt.get("_source", {}).get("layers", {}).get("ip", {}).get("ip.dst", "unknown"),
                    "protocol": pkt.get("_source", {}).get("layers", {}).get("frame", {}).get("frame.protocols", "unknown").split(":")[-1].upper(),
                    "length": pkt.get("_source", {}).get("layers", {}).get("frame", {}).get("frame.len", 0)
                }
                for pkt in packets[:10] # Return top 10 for display
            ]
        }

    async def get_baseline(self) -> dict[str, Any]:
        """Get the current baseline data."""
        return self._baseline_data.copy()

    async def reset_baseline(self) -> None:
        """Reset the baseline data."""
        self._baseline_data = {}
        self._logger.info("baseline_reset")
