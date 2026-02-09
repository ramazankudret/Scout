"""
Netdiscover tool - active/passive ARP reconnaissance for LAN discovery.
"""
import asyncio
import re
import logging
from typing import Dict, Any, List

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class NetdiscoverTool(BaseTool):
    name = "netdiscover"
    description = "Discover hosts on local network via ARP. Use netdiscover binary (-P -N for parseable output)."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ip_range": {"type": "string", "description": "IP range (e.g. 192.168.1.0/24 or 192.168.1.1-20)"},
                "interface": {"type": "string", "description": "Network interface (e.g. eth0)"},
            },
            "required": [],
        }

    async def run(
        self,
        ip_range: str = "192.168.1.0/24",
        interface: str | None = None,
    ) -> ToolResult:
        """Run netdiscover with -P (parseable) -N (no header). Parse IP, MAC, vendor."""
        logger.info("Starting Netdiscover ip_range=%s", ip_range)
        try:
            args = ["netdiscover", "-r", ip_range, "-P", "-N"]
            if interface:
                args.extend(["-i", interface])
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)
            out = (stdout or b"").decode()
            err = (stderr or b"").decode()
            if proc.returncode != 0 and err:
                logger.warning("Netdiscover stderr: %s", err)
            # Parse lines like "  192.168.1.1    00:11:22:33:44:55    vendor"
            hosts: List[Dict[str, str]] = []
            for line in out.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                # Typical: IP at start, then MAC, then rest is vendor
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[0]
                    mac = parts[1] if len(parts) > 1 else ""
                    vendor = " ".join(parts[2:]) if len(parts) > 2 else ""
                    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                        hosts.append({"ip": ip, "mac": mac, "vendor": vendor})
            return ToolResult(success=True, data={"hosts": hosts, "count": len(hosts)})
        except FileNotFoundError:
            logger.error("netdiscover binary not found")
            return ToolResult(success=False, error="netdiscover not installed or not in PATH")
        except asyncio.TimeoutError:
            logger.error("Netdiscover timeout")
            return ToolResult(success=False, error="netdiscover timeout (120s)")
        except Exception as e:
            logger.error("Netdiscover failed: %s", e)
            return ToolResult(success=False, error=str(e))
