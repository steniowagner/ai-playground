from langchain.messages import HumanMessage

from triage_ops.graph.state import State


def get_latest_user_message(state: State) -> HumanMessage | None:
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            return message

    return None
