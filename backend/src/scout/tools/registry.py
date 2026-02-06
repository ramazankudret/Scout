from typing import Any, Dict, List, Type
from .base import BaseTool
from .nmap import NmapTool
from .wireshark import TsharkTool
from .masscan import MasscanTool
from .netdiscover import NetdiscoverTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        self.register(NmapTool())
        self.register(TsharkTool())
        self.register(MasscanTool())
        self.register(NetdiscoverTool())
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> BaseTool:
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name, 
                "description": tool.description,
                "schema": tool.schema
            } 
            for tool in self._tools.values()
        ]

    def get_tools_for_langchain(self) -> List[Any]:
        """
        Converts registered tools to LangChain compatible tools.
        (This will be implemented when we integrate with Agents)
        """
        # Placeholder for future integration
        pass

# Global instance
tool_registry = ToolRegistry()
