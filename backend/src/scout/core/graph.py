from langgraph.graph import StateGraph, END
from scout.core.state import AgentState
from scout.agents.implementations import OrchestratorAgent, HunterAgent, StealthAgent, DefenseAgent

# Initialize agents
orchestrator = OrchestratorAgent()
hunter = HunterAgent()
stealth = StealthAgent()
defense = DefenseAgent()

async def run_orchestrator(state: AgentState):
    return await orchestrator.run(state)

async def run_hunter(state: AgentState):
    return await hunter.run(state)

async def run_stealth(state: AgentState):
    return await stealth.run(state)

async def run_defense(state: AgentState):
    return await defense.run(state)

def router(state: AgentState):
    """
    Router function to determine the next node based on current_agent state.
    """
    next_agent = state.get("current_agent", "end")
    if next_agent == "hunter":
        return "hunter"
    elif next_agent == "stealth":
        return "stealth"
    elif next_agent == "defense":
        return "defense"
    elif next_agent == "orchestrator":
        return "orchestrator"
    else:
        return "end"

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("orchestrator", run_orchestrator)
workflow.add_node("hunter", run_hunter)
workflow.add_node("stealth", run_stealth)
workflow.add_node("defense", run_defense)

# Set entry point
workflow.set_entry_point("orchestrator")

# Add conditional edges from Orchestrator
workflow.add_conditional_edges(
    "orchestrator",
    router,
    {
        "hunter": "hunter",
        "stealth": "stealth",
        "defense": "defense",
        "end": END,
        "orchestrator": "orchestrator" # Should not happen usually, but for safety
    }
)

# Add edges from workers back to Orchestrator (loop)
workflow.add_edge("hunter", "orchestrator")
workflow.add_edge("stealth", "orchestrator")
workflow.add_edge("defense", "orchestrator")

# Compile the graph
agent_graph = workflow.compile()
