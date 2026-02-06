"""
Masscan tool - fast port scanner for large ranges.
"""
import asyncio
import re
import logging
from typing import Dict, Any

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class MasscanTool(BaseTool):
    name = "masscan_scanner"
    description = "Fast port scanner for IP ranges (e.g. 192.168.0.0/24). Use masscan binary."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "targets": {"type": "string", "description": "Target IP or CIDR (e.g. 192.168.1.0/24 or 10.0.0.1)"},
                "ports": {"type": "string", "description": "Port range (default: 1-1000)"},
                "rate": {"type": "integer", "description": "Packets per second (default: 1000)"},
            },
            "required": ["targets"],
        }

    async def run(
        self,
        targets: str,
        ports: str = "1-1000",
        rate: int = 1000,
    ) -> ToolResult:
        """Run masscan. Output format: -oL (list), parse 'open tcp PORT IP TIMESTAMP'."""
        logger.info("Starting Masscan on %s ports=%s rate=%s", targets, ports, rate)
        try:
            proc = await asyncio.create_subprocess_exec(
                "masscan",
                targets,
                "-p", ports,
                "--rate", str(rate),
                "-oL", "-",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0 and proc.returncode != 255:
                # masscan returns 255 when no results sometimes
                err = stderr.decode() if stderr else ""
                logger.warning("Masscan exit code %s: %s", proc.returncode, err)
            out = (stdout or b"").decode()
            # Parse -oL: "open tcp 80 192.168.1.1 1234567890"
            hosts: Dict[str, Dict[str, Any]] = {}
            for line in out.strip().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 5 and parts[0] == "open" and parts[1] == "tcp":
                    port = int(parts[2])
                    ip = parts[3]
                    if ip not in hosts:
                        hosts[ip] = {"tcp": {}, "open_ports": []}
                    hosts[ip]["tcp"][str(port)] = {"name": "", "state": "open"}
                    if port not in hosts[ip]["open_ports"]:
                        hosts[ip]["open_ports"].append(port)
            for ip in hosts:
                hosts[ip]["open_ports"] = sorted(hosts[ip]["open_ports"])
            return ToolResult(success=True, data={"hosts": hosts, "command": f"masscan {targets} -p{ports} --rate {rate}"})
        except FileNotFoundError:
            logger.error("masscan binary not found")
            return ToolResult(success=False, error="masscan not installed or not in PATH")
        except Exception as e:
            logger.error("Masscan failed: %s", e)
            return ToolResult(success=False, error=str(e))
