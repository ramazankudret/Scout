"""
Scapy-based packet sniffer.

Captures packets and returns them in the same format as packet_logs
(source_ip, destination_ip, protocol, length, etc.) for TrafficRepository.save_batch.
"""
import asyncio
import logging
from typing import Any, Dict, List

from scout.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


def _sniff_blocking(
    interface: str,
    packet_count: int,
    timeout_sec: int,
) -> List[Dict[str, Any]]:
    """Run scapy sniff in a thread; returns list of packet_log-style dicts."""
    try:
        from scapy.all import sniff
        from scapy.layers.inet import IP
    except ImportError as e:
        raise RuntimeError(f"Scapy not installed: {e}") from e

    packets_out: List[Dict[str, Any]] = []

    def _process(pkt: Any) -> None:
        src_ip = "0.0.0.0"
        dst_ip = "0.0.0.0"
        protocol = "unknown"
        if pkt.haslayer(IP):
            src_ip = pkt[IP].src or src_ip
            dst_ip = pkt[IP].dst or dst_ip
            if pkt.haslayer("TCP"):
                protocol = "TCP"
            elif pkt.haslayer("UDP"):
                protocol = "UDP"
            elif pkt.haslayer("ICMP"):
                protocol = "ICMP"
            else:
                protocol = (pkt[IP].proto or "unknown").__str__()[:20]
        length = len(pkt)
        packets_out.append({
            "source_ip": src_ip,
            "destination_ip": dst_ip,
            "protocol": protocol,
            "length": length,
            "info": "",
            "interface": interface,
            "direction": "unknown",
        })

    try:
        sniff(
            iface=interface if interface else None,
            count=packet_count,
            timeout=timeout_sec,
            prn=_process,
            store=False,
        )
    except Exception as e:
        logger.warning("scapy_sniff_error", error=str(e))
        raise
    return packets_out


class ScapySnifferTool(BaseTool):
    name = "scapy_sniffer"
    description = "Captures network traffic using Scapy and returns packet summaries (packet_logs format)."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "interface": {"type": "string", "description": "Network interface (e.g. eth0, ETHERNET)"},
                "packet_count": {"type": "integer", "description": "Number of packets to capture (default: 100)"},
                "duration": {"type": "integer", "description": "Max duration in seconds (default: 10)"},
            },
            "required": [],
        }

    async def run(
        self,
        interface: str = "eth0",
        packet_count: int = 100,
        duration: int = 10,
        **kwargs: Any,
    ) -> ToolResult:
        """Capture packets with Scapy; return data in packet_logs format for save_batch."""
        logger.info("scapy_sniffer_start", interface=interface, packet_count=packet_count, duration=duration)
        loop = asyncio.get_event_loop()
        try:
            packets = await loop.run_in_executor(
                None,
                lambda: _sniff_blocking(
                    interface=interface,
                    packet_count=packet_count,
                    timeout_sec=duration or 10,
                ),
            )
        except RuntimeError as e:
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            logger.exception("scapy_sniffer_failed")
            return ToolResult(success=False, error=str(e))
        logger.info("scapy_sniffer_done", count=len(packets))
        return ToolResult(success=True, data={"packets": packets})
