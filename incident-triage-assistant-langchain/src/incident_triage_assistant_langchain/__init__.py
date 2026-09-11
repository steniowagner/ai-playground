import json
from functools import partial

from dotenv import load_dotenv
from langchain.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from incident_triage_assistant_langchain.conditions.after_finalize_investigation import (
    after_finalize_investigation,
)
from incident_triage_assistant_langchain.conditions.after_llm_call import (
    after_llm_call,
)
from incident_triage_assistant_langchain.conditions.after_tool_call import (
    after_tool_call,
)
from incident_triage_assistant_langchain.graph.events import StreamEvents
from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationResponse,
)
from incident_triage_assistant_langchain.nodes.execute_approvals.node import (
    execute_approvals_node,
)
from incident_triage_assistant_langchain.nodes.finalize_investigation.node import (
    finalize_investigation_node,
)
from incident_triage_assistant_langchain.nodes.llm_call.node import llm_call_node
from incident_triage_assistant_langchain.nodes.prepare_approvals.node import (
    prepare_approvals_node,
)
from incident_triage_assistant_langchain.nodes.request_approvals.node import (
    request_approvals_node,
)
from incident_triage_assistant_langchain.nodes.schema import Nodes
from incident_triage_assistant_langchain.nodes.tool_calls.node import (
    tool_calls_node,
)
from incident_triage_assistant_langchain.services.rollback_deployment.service import (
    RollbackDeploymentServiceArgs,
    RoolbackDeploymentService,
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
    service_registry = bootstrap_services()

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
    graph.add_node(Nodes.PREPARE_APPROVALS, prepare_approvals_node)
    graph.add_node(Nodes.REQUEST_APPROVALS, request_approvals_node)
    graph.add_node(
        Nodes.EXECUTE_APPROVALS,
        partial(execute_approvals_node, service_registry=service_registry),
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
    graph.add_conditional_edges(
        Nodes.FINALIZER,
        after_finalize_investigation,
        [Nodes.PREPARE_APPROVALS, END],
    )
    graph.add_edge(Nodes.PREPARE_APPROVALS, Nodes.REQUEST_APPROVALS)
    graph.add_edge(Nodes.REQUEST_APPROVALS, Nodes.EXECUTE_APPROVALS)
    graph.add_edge(Nodes.EXECUTE_APPROVALS, END)

    return graph.compile(checkpointer=InMemorySaver())


def main() -> None:
    load_dotenv()

    graph_agent = build_graph()

    config: RunnableConfig = {
        "configurable": {
            "thread_id": "cli-session",
        },
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

        # The first graph input is the user's message.
        graph_input = {
            "messages": [HumanMessage(content=user_input)],
            "final_result": None,
        }

        # This inner loop allows the same graph execution to be resumed
        # after one or more interrupts.
        while graph_input is not None:
            approval_request = None

            for mode, payload in graph_agent.stream(
                input=graph_input,
                config=config,
                stream_mode=["messages", "updates", "custom"],
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
                        print(
                            f"[Thinking] {thinking}",
                            end="",
                            flush=True,
                        )
                        print()

                    if answer:
                        print(
                            f"[Answer] {answer}",
                            end="",
                            flush=True,
                        )
                        print()

                elif mode == "updates":
                    # LangGraph reports an interrupt as a special update.
                    if "__interrupt__" in payload:
                        interruptions = payload["__interrupt__"]

                        if interruptions:
                            approval_request = interruptions[0].value

                        continue

                    for node_name, update in payload.items():
                        if node_name == Nodes.FINALIZER:
                            final_result = update.get("final_result")

                elif mode == "custom":
                    event = payload.get("event")

                    if event == StreamEvents.TOOL_STARTED:
                        args = json.dumps(
                            payload["args"],
                            sort_keys=True,
                        )

                        print(
                            f"{payload['tool']} {args}",
                            flush=True,
                        )

                    elif event == StreamEvents.TOOL_FINISHED:
                        mark = "ok" if payload["ok"] else payload["code"]

                        print(
                            f"      → {mark}",
                            flush=True,
                        )

                    elif event in (
                        StreamEvents.TOOL_FAIELD,
                        StreamEvents.TOOL_SKIPPED,
                    ):
                        print(
                            f"      → {payload.get('code') or payload.get('reason')}",
                            flush=True,
                        )

            if approval_request is None:
                # No interruption means the graph reached END.
                graph_input = None
                continue

            actions = approval_request.get("actions", [])
            decisions = []

            print()
            print("The investigation proposed the following actions:")

            for index, action in enumerate(actions, start=1):
                print()
                print(f"Action {index}")
                print(f"Type: {action['kind']}")
                print(f"Incident: {action['incident_id']}")
                print(f"Reason: {action['rationale']}")
                print("Arguments:")
                print(
                    json.dumps(
                        action["args"],
                        indent=2,
                        sort_keys=True,
                    )
                )

                while True:
                    try:
                        answer = input("Approve this action? [y/n] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        return

                    if answer in ("y", "yes"):
                        approved = True
                        break

                    if answer in ("n", "no"):
                        approved = False
                        break

                    print("Please enter 'y' or 'n'.")

                decisions.append(
                    {
                        # This ID was generated by prepare_approvals_node
                        # and returned in the interrupt payload.
                        "proposal_id": action["proposal_id"],
                        "approved": approved,
                    }
                )

            # On the next inner-loop iteration, this is passed to the
            # same graph with the same thread_id.
            graph_input = Command(
                resume={
                    "decisions": decisions,
                }
            )

        if final_result is not None:
            print()
            print(final_result.model_dump_json(indent=2))
