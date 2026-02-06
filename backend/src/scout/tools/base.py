from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ToolResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_output: Optional[str] = None

class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool description"
    
    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments"""
        pass
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Return JSON schema for the tool arguments (for LLM)"""
        return {}
