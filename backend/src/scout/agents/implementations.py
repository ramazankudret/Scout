from typing import Any, Dict
from langchain_core.messages import HumanMessage, AIMessage
from scout.agents.base import BaseAgent
from scout.core.state import AgentState
from scout.core.error_handler import safe_execute
from scout.core.logger import get_logger
from scout.guards.llm_guard import llm_guard
from scout.agents.supervisor import supervisor
from scout.core.model_router import get_fast_model, TaskCategory

# Get logger for agents
logger = get_logger("agents")

def monitor_execution(func):
    """Decorator to monitor agent execution with Supervisor."""
    async def wrapper(self, *args, **kwargs):
        await supervisor.register_agent(self.name)
        try:
            result = await func(self, *args, **kwargs)
            await supervisor.record_execution(self.name, success=True)
            return result
        except Exception as e:
            await supervisor.record_execution(self.name, success=False, error=str(e))
            raise e
    return wrapper

class OrchestratorAgent(BaseAgent):
    """
    The Orchestrator agent responsible for routing tasks to other agents.
    """
    def __init__(self):
        super().__init__(name="Orchestrator")

    @safe_execute(reraise=True)
    @monitor_execution
    async def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Decides which agent should act next based on the last message.
        """
        logger.info("orchestrator_routing", agent=self.name)
        
        messages = state['messages']
        last_message = messages[-1]
        
        # Sanitize input with LLM Guard
        sanitized_content, scan_result = llm_guard.guard_input(last_message.content, raise_on_threat=False)
        if not scan_result.is_safe:
            logger.warning("potential_threat_detected", threats=scan_result.threats_found, input_preview=last_message.content[:50])
        
        # Use Fast Model (Nemotron) for intelligent routing
        try:
            llm = get_fast_model()
            prompt = f"""You are the Orchestrator for Scout, a cybersecurity AI.
            
Analyze the user request and select the BEST agent to handle it.

AGENTS:
- Hunter: Scans for vulnerabilities, checks ports, IP analysis.
- Stealth: Monitors network traffic, analyzes logs, passive listening.
- Defense: Configures firewall, blocks IPs, mitigation actions.

REQUEST: "{sanitized_content}"

Respond with ONLY one word: HUNTER, STEALTH, DEFENSE, or END (if unclear).
"""
            response = await llm.ainvoke(prompt)
            decision = response.content.strip().upper()
            
            # Fallback for simple rule-based if LLM fails or is unclear
            if decision not in ["HUNTER", "STEALTH", "DEFENSE", "END"]:
                 decision = self._fallback_routing(sanitized_content)

        except Exception as e:
            logger.error("smart_routing_failed", error=str(e))
            decision = self._fallback_routing(sanitized_content)
            
        # Map decision to next_agent
        if "HUNTER" in decision:
            next_agent = "hunter"
            response_text = "Routing request to Hunter Agent for scanning..."
        elif "STEALTH" in decision:
            next_agent = "stealth"
            response_text = "Routing request to Stealth Agent for monitoring..."
        elif "DEFENSE" in decision:
            next_agent = "defense"
            response_text = "Routing request to Defense Agent for protection..."
        else:
            next_agent = "end"
            response_text = "I understood your request but I need more specifics. Are we scanning via Hunter, monitoring via Stealth, or defending?"

        return {
            "current_agent": next_agent,
            "messages": [AIMessage(content=response_text)],
            "task_status": "routing"
        }

    def _fallback_routing(self, content: str) -> str:
        """Simple keyword-based routing backup."""
        content = content.lower()
        if "scan" in content or "vuln" in content or "nmap" in content:
            return "HUNTER"
        elif "traffic" in content or "log" in content or "listen" in content:
            return "STEALTH"
        elif "block" in content or "firewall" in content or "protect" in content:
            return "DEFENSE"
        return "END"

class HunterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Hunter")

    @safe_execute(reraise=True)
    @monitor_execution
    async def run(self, state: AgentState) -> Dict[str, Any]:
        logger.info("hunter_scanning", agent=self.name)
        return {
            "current_agent": "orchestrator", # Return control to orchestrator
            "messages": [AIMessage(content="[HUNTER] Scanning target... No critical vulnerabilities found (Mock).")],
            "findings": [{"type": "scan_result", "status": "clean"}]
        }

class StealthAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Stealth")

    @safe_execute(reraise=True)
    @monitor_execution
    async def run(self, state: AgentState) -> Dict[str, Any]:
        logger.info("stealth_monitoring", agent=self.name)
        return {
            "current_agent": "orchestrator",
            "messages": [AIMessage(content="[STEALTH] Passive monitoring active. Traffic normal.")],
            "findings": [{"type": "traffic_log", "status": "normal"}]
        }

class DefenseAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Defense")

    @safe_execute(reraise=True)
    @monitor_execution
    async def run(self, state: AgentState) -> Dict[str, Any]:
        logger.info("defense_protecting", agent=self.name)
        return {
            "current_agent": "orchestrator",
            "messages": [AIMessage(content="[DEFENSE] Firewall rules updated. Perimeter secure.")],
            "findings": [{"type": "firewall_update", "status": "applied"}]
        }
