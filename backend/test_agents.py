import asyncio
from langchain_core.messages import HumanMessage
from scout.core.graph import agent_graph

async def test_multi_agent():
    print("🤖 Scout Multi-Agent System Test")
    print("--------------------------------")
    
    # Test Case 1: Scanning Request
    print("\n[USER]: Scan target 192.168.1.10")
    initial_state = {
        "messages": [HumanMessage(content="Please scan target 192.168.1.10 for vulnerabilities")],
        "current_agent": "orchestrator",
        "findings": [],
        "task_status": "started",
        "shared_context": {}
    }
    
    async for event in agent_graph.astream(initial_state):
        for key, value in event.items():
            print(f"  └── Node: {key}")
            if "messages" in value:
                print(f"      Message: {value['messages'][0].content}")
                
    # Test Case 2: Defense Request
    print("\n[USER]: Update firewall rules")
    initial_state = {
        "messages": [HumanMessage(content="Update firewall rules to block port 8080")],
        "current_agent": "orchestrator",
        "findings": [],
        "task_status": "started",
        "shared_context": {}
    }
    
    async for event in agent_graph.astream(initial_state):
        for key, value in event.items():
            print(f"  └── Node: {key}")
            if "messages" in value:
                print(f"      Message: {value['messages'][0].content}")

if __name__ == "__main__":
    asyncio.run(test_multi_agent())
