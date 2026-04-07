from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from llm import LLMConfig, RoleAwareChatModelFactory
from agents import (
    build_compliance_officer_node,
    build_creator_node,
    build_researcher_node,
    build_research_tools_node,
)
from state import AnalysisState


def build_graph(
    researcher_model: BaseChatModel,
    creator_model: BaseChatModel,
    compliance_officer_model: BaseChatModel,
):
    graph = StateGraph(AnalysisState)
    graph.add_node("researcher", build_researcher_node(researcher_model))
    graph.add_node("research_tools", build_research_tools_node())
    graph.add_node("creator", build_creator_node(creator_model))
    graph.add_node(
        "compliance_officer",
        build_compliance_officer_node(compliance_officer_model),
    )
    graph.add_edge(START, "researcher")
    graph.add_conditional_edges(
        "researcher",
        route_after_researcher,
        {
            "research_tools": "research_tools",
            "creator": "creator",
            "end": END,
        },
    )
    graph.add_edge("research_tools", "researcher")
    graph.add_edge("creator", "compliance_officer")
    graph.add_conditional_edges(
        "compliance_officer",
        route_after_compliance,
        {
            "creator": "creator",
            "end": END,
        },
    )
    return graph.compile()


def route_after_researcher(state: AnalysisState) -> str:
    messages = list(state.get("messages", []))
    if not messages:
        return "creator"

    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
        return "research_tools"
    if state.get("research_status") == "blocked":
        return "end"
    return "creator"


def route_after_compliance(state: AnalysisState) -> str:
    if state.get("compliance_status") == "needs_revision":
        if state.get("revision_count", 0) < state.get("max_revisions", 2):
            return "creator"
    return "end"


def run_analysis(
    offer_url: str,
    traffic_source: str,
    llm_config: LLMConfig,
) -> AnalysisState:
    factory = RoleAwareChatModelFactory(llm_config)
    app = build_graph(
        researcher_model=factory.create_chat_model("researcher"),
        creator_model=factory.create_chat_model("creator"),
        compliance_officer_model=factory.create_chat_model("compliance_officer"),
    )
    initial_state: AnalysisState = {
        "offer_url": offer_url,
        "traffic_source": traffic_source,
    }
    return app.invoke(initial_state)
