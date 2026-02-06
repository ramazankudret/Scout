import nmap
import asyncio
from typing import Dict, Any, List
from .base import BaseTool, ToolResult
import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"Starting Nmap scan on {hosts} with args: {arguments}")
        
        try:
            # nmap python library is synchronous, so we run it in a thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.nm.scan(hosts=hosts, arguments=arguments)
            )
            
            # Simple parsing/processing can be added here if needed
            scan_data = {
                "command": self.nm.command_line(),
                "scan_info": self.nm.scaninfo(),
                "hosts": {}
            }
            
            for host in self.nm.all_hosts():
                scan_data["hosts"][host] = self.nm[host]

            logger.info(f"Nmap scan completed for {hosts}")
            return ToolResult(success=True, data=scan_data)

        except Exception as e:
            logger.error(f"Nmap scan failed: {str(e)}")
            return ToolResult(success=False, error=str(e))
