from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict
from shared.types import AgentState

# Processing nodes
from nodes.classify import classify_node
from nodes.order import extract_order_node
from nodes.shipping import extract_shipping_node
from nodes.shipping_update import extract_shipping_update_node
from nodes.refund import extract_refund_node
from nodes.return_confirmation import extract_return_confirmation_node
from nodes.return_update import extract_return_update_node

# ----------------------------------------
# 🧠 Define LangGraph pipeline for email classification and extraction
# ----------------------------------------

email_graph = StateGraph(AgentState)

# Register all task nodes
email_graph.add_node("classify", classify_node)
email_graph.add_node("order", extract_order_node)
email_graph.add_node("refund", extract_refund_node)
email_graph.add_node("shipping", extract_shipping_node)
email_graph.add_node("shipping_update", extract_shipping_update_node)
email_graph.add_node("return_confirmation", extract_return_confirmation_node)
email_graph.add_node("return_update", extract_return_update_node)

# Set entry point
email_graph.set_entry_point("classify")


def router(state: AgentState) -> str:
    """
    Route classified email to its respective processing node.

    Args:
        state (AgentState): Current state with `category` key

    Returns:
        str: Node name to transition to, or END
    """
    category = (state.get("category") or "").lower()

    if "order confirmation" in category:
        return "order"
    if "refund" in category:
        return "refund"
    if "shipping confirmation" in category or "order update" in category:
        return "shipping"
    if "shipping update" in category:
        return "shipping_update"
    if "return update" in category:
        return "return_update"
    if "return confirmation" in category:
        return "return_confirmation"

    # Ignored or unsupported categories
    if category in {"promos", "goods receipt", "services receipt"}:
        return END

    return END


# Define flow transitions
email_graph.add_conditional_edges("classify", router)
email_graph.add_edge("order", END)
email_graph.add_edge("refund", END)
email_graph.add_edge("shipping", END)
email_graph.add_edge("shipping_update", END)
email_graph.add_edge("return_confirmation", END)
email_graph.add_edge("return_update", END)

# Compile the LangGraph workflow
workflow = email_graph.compile(checkpointer=MemorySaver())
