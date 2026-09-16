from langchain.messages import AIMessage
from langgraph.config import get_stream_writer

from triage_ops.graph import State
from triage_ops.graph.event_stream import CustomStreamEvents

OUT_OF_SCOPE_RESPONSE = (
    "I can help with incident triage and operational questions about services, "
    "deployments, logs, metrics, feature flags, maintenance windows, and "
    "runbooks. Please ask me about one of those areas."
)


def reject_out_of_scope_node(_: State) -> dict:
    writer = get_stream_writer()

    writer(
        {
            "event": CustomStreamEvents.MESSAGE_CHUNK,
            "content": OUT_OF_SCOPE_RESPONSE,
        }
    )

    return {
        "messages": [
            AIMessage(content=OUT_OF_SCOPE_RESPONSE),
        ]
    }
