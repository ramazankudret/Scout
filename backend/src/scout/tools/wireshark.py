import asyncio
import json
import logging
from typing import Dict, Any, List
from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class TsharkTool(BaseTool):
    name = "traffic_sniffer"
    description = "Captures network traffic using Tshark (Wireshark) and returns packet summaries."
    
    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "interface": {"type": "string", "description": "Network interface to listen on (default: eth0)"},
                "packet_count": {"type": "integer", "description": "Number of packets to capture (default: 100)"},
                "duration": {"type": "integer", "description": "Duration in seconds to capture (optional override)"},
                "filter": {"type": "string", "description": "BPF capture filter (e.g., 'tcp port 80')"}
            },
            "required": []
        }

    async def run(self, interface: str = "eth0", packet_count: int = 100, duration: int = None, filter: str = "") -> ToolResult:
        """
        Runs Tshark asynchronously.
        """
        logger.info(f"Starting Tshark capture on {interface}, count={packet_count}, filter='{filter}'")
        
        args = [
            "tshark",
            "-i", interface,
            "-T", "json",
            "-c", str(packet_count)
        ]
        
        if duration:
            args.extend(["-a", f"duration:{duration}"])
            
        if filter:
            args.extend(["-f", filter])

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Tshark failed: {error_msg}")
                return ToolResult(success=False, error=error_msg)
                
            output_data = stdout.decode()
            try:
                raw = json.loads(output_data)
                # Tshark -T json: array of packets, or single packet object
                if isinstance(raw, list):
                    packets = raw
                elif isinstance(raw, dict) and "packets" in raw:
                    packets = raw["packets"] if isinstance(raw["packets"], list) else [raw["packets"]]
                else:
                    packets = [raw] if raw else []
                logger.info(f"Captured {len(packets)} packets")
                return ToolResult(success=True, data={"packets": packets})
            except json.JSONDecodeError:
                logger.warning("Could not decode Tshark JSON output")
                return ToolResult(success=True, data={"packets": []}, raw_output=output_data)

        except Exception as e:
            logger.error(f"Tshark execution error: {str(e)}")
            return ToolResult(success=False, error=str(e))
