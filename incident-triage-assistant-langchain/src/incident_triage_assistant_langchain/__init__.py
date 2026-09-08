from functools import partial

from dotenv import load_dotenv
from langchain.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from incident_triage_assistant_langchain.conditions.after_llm_call import (
    after_llm_call,
)
from incident_triage_assistant_langchain.conditions.after_tool_call import (
    after_tool_call,
)
from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationResponse,
)
from incident_triage_assistant_langchain.nodes.finalize_investigation.node import (
    finalize_investigation_node,
)
from incident_triage_assistant_langchain.nodes.llm_call.node import llm_call_node
from incident_triage_assistant_langchain.nodes.schema import Nodes
from incident_triage_assistant_langchain.nodes.tool_calls.node import (
    tool_calls_node,
)

from .state import State
from .tools.bootstrap_tools import bootstrap_tools

MODEL_NAME = "claude-haiku-4-5-20251001"


def split_stream_chunk(message_chunk) -> tuple[str, str]:
    content = message_chunk.content

    if isinstance(content, str):
        return "", content

    thinking_parts: list[str] = []
    answer_parts: list[str] = []

    for block in content:
        if not isinstance(block, dict):
            continue

        block_type = block.get("type")

        if block_type in ("thinking", "reasoning"):
            thinking_parts.append(block.get("thinking") or block.get("reasoning") or "")
        if block_type == "text":
            answer_parts.append(block.get("text", ""))

    return "".join(thinking_parts), "".join(answer_parts)


def build_graph():
    model = ChatAnthropic(
        model=MODEL_NAME,
        timeout=None,
        stop=None,
        thinking={"type": "enabled", "budget_tokens": 5000},
    )

    tools = bootstrap_tools()

    agent_model = model.bind_tools(tools)
    finalizer_model = model.with_structured_output(
        InvestigationResponse, method="json_schema"
    )

    graph = StateGraph(State)

    graph.add_node(
        Nodes.LLM_CALL,
        partial(llm_call_node, model=agent_model),
    )
    graph.add_node(
        Nodes.TOOL,
        partial(tool_calls_node, tools={tool.get_name(): tool for tool in tools}),
    )
    graph.add_node(
        Nodes.FINALIZER,
        partial(finalize_investigation_node, model=finalizer_model),
    )

    graph.add_edge(START, Nodes.LLM_CALL)
    graph.add_conditional_edges(
        Nodes.LLM_CALL,
        after_llm_call,
        [Nodes.TOOL, END],
    )
    graph.add_conditional_edges(
        Nodes.TOOL,
        after_tool_call,
        [Nodes.LLM_CALL, Nodes.FINALIZER],
    )
    graph.add_edge(Nodes.FINALIZER, END)

    return graph.compile(checkpointer=InMemorySaver())


def main() -> None:
    load_dotenv()

    graph_agent = build_graph()

    config: RunnableConfig = {
        "configurable": {"thread_id": "cli-session"},
    }

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if not user_input:
            continue

        if user_input.lower() == "exit":
            return

        final_result = None

        for mode, payload in graph_agent.stream(
            input={
                "messages": [HumanMessage(content=user_input)],
                "final_result": None,
            },
            config=config,
            stream_mode=["messages", "updates"],
        ):
            if mode == "messages":
                message_chunk, metadata = payload

                node = metadata.get("langgraph_node")
                if node not in (
                    Nodes.LLM_CALL,
                    Nodes.FINALIZER,
                ):
                    continue

                thinking, answer = split_stream_chunk(message_chunk)
                if thinking:
                    print(f"[Thinking] {thinking}", end="", flush=True)
                    print()
                if answer:
                    print(f"[Answer] {answer}", end="", flush=True)
                    print()

            elif mode == "updates":
                for node_name, update in payload.items():
                    if node_name == Nodes.FINALIZER:
                        final_result = update.get("final_result")

        if final_result is not None:
            print(final_result.model_dump_json(indent=2))
