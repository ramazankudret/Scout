"""
Agent chat API.

Exposes the agent graph (Orchestrator → Hunter/Stealth/Defense) via POST /agent/chat.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from scout.core.graph import agent_graph
from scout.core.logging import get_logger
from scout.core.state import AgentState

router = APIRouter()
logger = get_logger(__name__)


class AgentChatRequest(BaseModel):
    """Request body for agent chat."""

    message: str = Field(..., min_length=1, max_length=4000)


class AgentChatResponse(BaseModel):
    """Response for agent chat."""

    response: str
    current_agent: str
    findings: list[dict[str, Any]] = Field(default_factory=list)


def _last_ai_content(messages: list[BaseMessage]) -> str:
    """Get content of the last AI message, or empty string."""
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            return m.content if isinstance(m.content, str) else str(m.content)
    return "No response from agents."


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest) -> AgentChatResponse:
    """
    Send a message to the agent graph (Orchestrator → Hunter/Stealth/Defense).

    The graph routes to the appropriate agent and returns the response
    plus which agent last responded.
    """
    try:
        initial_state: AgentState = {
            "messages": [HumanMessage(content=request.message)],
            "current_agent": "orchestrator",
            "shared_context": {},
            "findings": [],
            "task_status": "started",
        }
        final_state = await agent_graph.ainvoke(
            initial_state,
            config={"recursion_limit": 50},
        )
        messages = final_state.get("messages") or []
        response_text = _last_ai_content(messages)
        current_agent = final_state.get("current_agent") or "end"
        findings = final_state.get("findings") or []
        return AgentChatResponse(
            response=response_text,
            current_agent=current_agent,
            findings=findings,
        )
    except Exception as e:
        logger.error("agent_chat_error", error=str(e))
        err_str = str(e).lower()
        if "recursion" in err_str:
            detail = (
                "Ajan döngüye girdi (recursion limit). Lütfen daha kısa veya net bir istek yazın, "
                "veya tekrar deneyin."
            )
        elif "ollama" in err_str or "connection" in err_str or "llm" in err_str or "model" in err_str or "timeout" in err_str:
            detail = (
                "Ajan yanıtı şu an kullanılamıyor. Ollama'nın çalıştığından ve hızlı modelin "
                "(örn. nemotron-mini:4b) yüklü olduğundan emin olun."
            )
        else:
            detail = f"Ajan hatası: {e}"
        raise HTTPException(status_code=503, detail=detail) from e
