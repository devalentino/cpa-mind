from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from collections.abc import Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from state import AnalysisState


def _message_text(response: object) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()
    return str(content)


def _tool_result_to_message_content(tool_result: object) -> str:
    if is_dataclass(tool_result):
        return json.dumps(asdict(tool_result), indent=2)
    if isinstance(tool_result, (dict, list)):
        return json.dumps(tool_result, indent=2)
    return str(tool_result)


def _parse_compliance_result(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "needs_revision", "Empty compliance response."

    first_line = lines[0].upper()
    if "APPROVED" in first_line:
        status = "approved"
    else:
        status = "needs_revision"

    feedback = "\n".join(lines[1:]).strip()
    if not feedback:
        feedback = "No detailed feedback provided."
    return status, feedback


def _parse_research_result(text: str) -> tuple[str, str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "blocked", "empty_research_response", "Empty research response."

    first_line = lines[0].upper()
    if "STATUS: READY_FOR_CREATION" in first_line:
        status = "ready_for_creation"
    else:
        status = "blocked"

    if len(lines) > 1 and lines[1].upper().startswith("BLOCK_REASON:"):
        block_reason = lines[1].split(":", 1)[1].strip() or "unspecified"
        report_lines = lines[2:]
    else:
        block_reason = "none" if status == "ready_for_creation" else "unspecified"
        report_lines = lines[1:]

    report = "\n".join(report_lines).strip()
    if not report:
        report = text.strip()

    return status, block_reason, report


def build_researcher_node(
    model: BaseChatModel,
    research_tools: list[BaseTool],
) -> Callable[[AnalysisState], AnalysisState]:
    researcher_model = model.bind_tools(research_tools)

    def researcher_node(state: AnalysisState) -> AnalysisState:
        offer_url = state["offer_url"]
        traffic_source = state["traffic_source"]
        messages = list(state.get("messages", []))
        initial_messages: list[SystemMessage | HumanMessage] = []

        if not messages:
            initial_messages = [
                SystemMessage(
                    content=(
                        "You are the Researcher agent in a CPA marketing system. "
                        "You can use tools selectively to analyze the offer, landings, "
                        "audience, market, competitors, and trends. "
                        "Do not call tools blindly. Start with the minimum useful tool, "
                        "and stop early when the offer state makes further research unnecessary. "
                        "If the offer appears disabled, rejected, unavailable, or otherwise not viable, "
                        "explain that and skip irrelevant downstream checks. "
                        "When you are done and no more tools are needed, respond in exactly this format:\n"
                        "STATUS: READY_FOR_CREATION or STATUS: BLOCKED\n"
                        "BLOCK_REASON: <reason-or-none>\n"
                        "<final research report>\n"
                        "Use READY_FOR_CREATION only when downstream creative work should proceed."
                    )
                ),
                HumanMessage(
                    content=(
                        f"Analyze this offer.\n"
                        f"Offer URL: {offer_url}\n"
                        f"Traffic source: {traffic_source}"
                    )
                ),
            ]
            messages = list(initial_messages)

        response = researcher_model.invoke(messages)
        state_update: AnalysisState = {
            "messages": [*initial_messages, response],
            "revision_count": state.get("revision_count", 0),
            "max_revisions": state.get("max_revisions", 2),
        }

        if not getattr(response, "tool_calls", None):
            research_text = _message_text(response)
            research_status, research_block_reason, researcher_report = (
                _parse_research_result(research_text)
            )
            state_update["research_status"] = research_status
            state_update["research_block_reason"] = research_block_reason
            state_update["researcher_report"] = researcher_report

        return state_update

    return researcher_node


def build_research_tools_node(
    research_tools: list[BaseTool],
) -> Callable[[AnalysisState], AnalysisState]:
    research_tool_by_name = {tool.name: tool for tool in research_tools}

    def research_tools_node(state: AnalysisState) -> AnalysisState:
        messages = list(state.get("messages", []))
        if not messages:
            raise RuntimeError("Research tools node was called without any messages.")

        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            raise RuntimeError("Research tools node expected the last message to be an AIMessage.")

        tool_outputs = dict(state.get("research_tool_outputs", {}))
        tool_messages: list[ToolMessage] = []

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool = research_tool_by_name.get(tool_name)
            if tool is None:
                raise ValueError(f"Unsupported research tool requested: {tool_name}")

            tool_result = tool.invoke(tool_call["args"])
            tool_outputs[tool_name] = tool_result
            tool_messages.append(
                ToolMessage(
                    content=_tool_result_to_message_content(tool_result),
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
            )

        return {
            "messages": tool_messages,
            "research_tool_outputs": tool_outputs,
        }

    return research_tools_node


def build_creator_node(
    model: BaseChatModel,
) -> Callable[[AnalysisState], AnalysisState]:
    def creator_node(state: AnalysisState) -> AnalysisState:
        revision_count = state.get("revision_count", 0)
        compliance_feedback = state.get("compliance_feedback", "No feedback yet.")

        prompt = f"""
You are the Creator agent in a CPA marketing system.
Create ad messaging and creative directions using the research summary.
If compliance feedback is provided, revise the work to address it.
Keep the output practical and campaign-oriented.

Traffic source: {state["traffic_source"]}
Revision count: {revision_count}
Compliance feedback: {compliance_feedback}

Research summary:
{state["researcher_report"]}
""".strip()

        creator_output = _message_text(model.invoke(prompt))

        return {
            "creator_output": creator_output
        }

    return creator_node


def build_compliance_officer_node(
    model: BaseChatModel,
) -> Callable[[AnalysisState], AnalysisState]:
    def compliance_officer_node(state: AnalysisState) -> AnalysisState:
        revision_count = state.get("revision_count", 0)
        max_revisions = state.get("max_revisions", 2)

        prompt = f"""
You are the Compliance Officer agent.
Review the proposed ad copy and creative directions for Facebook ads policy risk.

Reply in this exact format:
STATUS: APPROVED
<short feedback>

or

STATUS: NEEDS_REVISION
<specific revision feedback>

Traffic source: {state["traffic_source"]}
Creator output:
{state["creator_output"]}
""".strip()

        compliance_text = _message_text(model.invoke(prompt))
        compliance_status, compliance_feedback = _parse_compliance_result(
            compliance_text
        )

        return {
            "revision_count": min(revision_count + 1, max_revisions),
            "compliance_status": compliance_status,
            "compliance_feedback": compliance_feedback,
            "compliance_report": compliance_text,
        }

    return compliance_officer_node
