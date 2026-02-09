import os
import sys
import nmap
import asyncio
from typing import Dict, Any, List
from .base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)

# On Windows, ensure Nmap is on PATH (e.g. Chocolatey: "C:\Program Files (x86)\Nmap")
if sys.platform == "win32":
    _nmap_dirs = [
        os.environ.get("NMAP_PATH"),
        r"C:\Program Files (x86)\Nmap",
        r"C:\Program Files\Nmap",
    ]
    for _d in _nmap_dirs:
        if _d and os.path.isdir(_d) and _d not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")
            break


def _to_serializable(obj: Any) -> Any:
    """Convert nmap result to JSON-serializable dict/list/primitive so API response never fails."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(x) for x in obj]
    if hasattr(obj, "items"):
        return {str(k): _to_serializable(v) for k, v in obj.items()}
    try:
        if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            return [_to_serializable(x) for x in obj]
    except Exception:
        pass
    return str(obj)

class NmapTool(BaseTool):
    name = "nmap_scanner"
    description = "Scans a network or host for open ports, services, and OS detection."
    
    def __init__(self):
        self.nm = nmap.PortScanner()

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hosts": {"type": "string", "description": "Target hosts (e.g., '192.168.1.1' or '192.168.1.0/24')"},
                "arguments": {"type": "string", "description": "Nmap arguments (default: '-sV -O -p- -T4')"}
            },
            "required": ["hosts"]
        }

    async def run(self, hosts: str, arguments: str = "-sV -O -p- -T4") -> ToolResult:
        """
        Runs Nmap scan asynchronously.
        """
        logger.info("Starting Nmap scan on %s with args: %s", hosts, arguments)

        def _do_scan() -> None:
            self.nm.scan(hosts=hosts, arguments=arguments)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _do_scan)
        except Exception as e:
            logger.exception("Nmap scan failed")
            return ToolResult(success=False, error=str(e))

        try:
            raw_command = self.nm.command_line()
            raw_scaninfo = self.nm.scaninfo()
            hosts_data: Dict[str, Any] = {}
            for host in self.nm.all_hosts():
                hosts_data[host] = _to_serializable(self.nm[host])
            scan_data: Dict[str, Any] = {
                "command": raw_command if isinstance(raw_command, str) else str(raw_command),
                "scan_info": _to_serializable(raw_scaninfo),
                "hosts": hosts_data,
            }
            logger.info("Nmap scan completed for %s", hosts)
            return ToolResult(success=True, data=scan_data)
        except Exception as e:
            logger.exception("Nmap result parsing failed")
            return ToolResult(success=False, error=str(e))
