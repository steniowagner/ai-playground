import json

from incident_triage_assistant_langchain.graph.stream.custom import (
    handle_custom_event,
)
from incident_triage_assistant_langchain.graph.stream.messages import (
    handle_message_event,
)
from incident_triage_assistant_langchain.graph.stream.update import handle_update_event
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from .schema import GraphInput, GraphRunResult


class GraphRunner:
    def __init__(self, graph: CompiledStateGraph) -> None:
        self._graph = graph

    def _run_graph_until_pause(
        self, config: RunnableConfig, graph_input: GraphInput
    ) -> GraphRunResult:
        result = GraphRunResult()

        for mode, payload in self._graph.stream(
            input=graph_input,
            config=config,
            stream_mode=["messages", "updates", "custom"],
        ):
            if mode == "messages":
                handle_message_event(payload)

            if mode == "custom":
                handle_custom_event(payload)

            if mode == "updates":
                update = handle_update_event(payload)

                if update.final_result is not None:
                    result.final_result = update.final_result

                if update.approval_request is not None:
                    result.approval_request = update.approval_request

        return result

    def _collect_approval_decisions(self, approval_request: dict) -> list[dict]:
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
                    "proposal_id": action["proposal_id"],
                    "approved": approved,
                }
            )

        return decisions

    def _run(self, thread_id: str, graph_input: GraphInput) -> GraphRunResult:
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            },
        }

        run_result = GraphRunResult()
        next_input = graph_input

        while True:
            stream_result = self._run_graph_until_pause(config, next_input)

            if stream_result.final_result is not None:
                run_result.final_result = stream_result.final_result

            if stream_result.approval_request is None:
                run_result.status = "completed"
                run_result.approval_request = None
                break

            run_result.status = "awaiting_approval"
            run_result.approval_request = stream_result.approval_request

            approval_decision = self._collect_approval_decisions(
                stream_result.approval_request
            )

            next_input = Command(
                resume={
                    "decisions": approval_decision,
                }
            )

        return run_result

    def start(self, thread_id: str, message: str) -> GraphRunResult:
        graph_input: GraphInput = {
            "messages": [HumanMessage(content=message)],
            "final_result": None,
        }

        return self._run(thread_id, graph_input)
