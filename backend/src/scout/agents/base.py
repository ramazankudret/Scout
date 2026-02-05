from typing import Any, Dict
from langchain_core.messages import SystemMessage
from scout.core.state import AgentState

class BaseAgent:
    """
    Base class for all Scout agents.
    """
    def __init__(self, name: str, model_name: str = "gpt-4o"):
        self.name = name
        # We will initialize the LLM here. usage:
        # self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.model_name = model_name
        
    async def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Main execution method for the agent.
        Override this method in subclasses.
        """
        raise NotImplementedError("Subclasses must implement run method")

    def _create_system_message(self, content: str) -> SystemMessage:
        return SystemMessage(content=f"You are {self.name}. {content}")
