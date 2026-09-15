import json

from incident_triage_assistant_langchain.graph.nodes.tool_calls.utils import (
    find_messages_since_last_human_message,
)
from incident_triage_assistant_langchain.graph.state import State
from incident_triage_assistant_langchain.tools.schema import ToolNames
from langchain.messages import AIMessage, HumanMessage, ToolMessage


def build_evidence_transcript(state: State) -> str:
    investigation_messages = find_messages_since_last_human_message(state.messages)

    lines: list[str] = [f"INVESTIGATION-ID: {state.authorized_incident_id}"]

    for message in investigation_messages:
        if isinstance(message, HumanMessage):
            lines.append(f"USER REQUEST:\n{message.text}")
            continue

        if isinstance(message, AIMessage):
            for tool_call in message.tool_calls:
                if tool_call["name"] == ToolNames.COMPLETE_INVESTIGATION:
                    continue

                arguments = json.dumps(tool_call["args"], sort_keys=True)
                lines.append(f"TOOL CALL: {tool_call['name']}({arguments})")
            continue

        if isinstance(message, ToolMessage):
            if message.name == ToolNames.COMPLETE_INVESTIGATION:
                continue

            lines.append(f"TOOL RESULT [{message.name}]:\n{message.text}")

    return "\n\n".join(lines)
