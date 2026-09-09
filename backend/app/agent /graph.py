from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import router_node, tool_execution_node, synthesis_node

def build_agent_graph():
    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("tool_executor", tool_execution_node)
    builder.add_node("synthesizer", synthesis_node)

    builder.set_entry_point("router")
    builder.add_edge("router", "tool_executor")
    builder.add_edge("tool_executor", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()

agent_graph = build_agent_graph()
