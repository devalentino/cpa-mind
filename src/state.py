from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

class AnalysisState(TypedDict, total=False):
    offer_url: str
    traffic_source: str
    messages: Annotated[list[AnyMessage], add_messages]
    research_tool_outputs: dict[str, Any]
    research_status: str
    research_block_reason: str
    researcher_report: str
    creator_output: str
    compliance_report: str
    compliance_feedback: str
    compliance_status: str
    revision_count: int
    max_revisions: int
