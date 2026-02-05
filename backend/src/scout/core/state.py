from typing import TypedDict, Annotated, List, Union, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    State definition for the multi-agent system.
    This state is passed between agents in the graph.
    """
    # Messages history (chat history between user and agents)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Current active agent name
    current_agent: str
    
    # Shared context/memory accessible by all agents
    shared_context: Dict[str, Any]
    
    # Detected threats or findings
    findings: List[Dict[str, Any]]
    
    # Task status tracking
    task_status: str
