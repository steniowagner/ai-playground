import json

from incident_triage_assistant_langchain.graph.nodes.tool_calls.utils import (
    find_messages_since_last_human_message,
)
from incident_triage_assistant_langchain.tools.complete_investigation.tool import (
    COMPLETE_INVESTIGATION_TOOL_NAME,
)
from langchain.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage


def build_evidence_transcript(messages: list[AnyMessage]) -> str:
    investigation_messages = find_messages_since_last_human_message(messages)

    lines: list[str] = []

    for message in investigation_messages:
        if isinstance(message, HumanMessage):
            lines.append(f"USER REQUEST:\n{message.text}")
            continue

        if isinstance(message, AIMessage):
            for tool_call in message.tool_calls:
                if tool_call["name"] == COMPLETE_INVESTIGATION_TOOL_NAME:
                    continue

                arguments = json.dumps(tool_call["args"], sort_keys=True)
                lines.append(f"TOOL CALL: {tool_call['name']}({arguments})")
            continue

        if isinstance(message, ToolMessage):
            if message.name == COMPLETE_INVESTIGATION_TOOL_NAME:
                continue

            lines.append(f"TOOL RESULT [{message.name}]:\n{message.text}")

    return "\n\n".join(lines)
