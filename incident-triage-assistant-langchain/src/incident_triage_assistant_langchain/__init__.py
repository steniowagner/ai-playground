from functools import partial

from dotenv import load_dotenv
from langchain.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

from incident_triage_assistant_langchain.conditions.should_continue import (
    should_continue,
)
from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationFailure,
    InvestigationResponse,
    InvestigationResult,
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


def main() -> InvestigationResult | InvestigationFailure:
    load_dotenv()

    model = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
    )

    tools = bootstrap_tools()
    agent_model = model.bind_tools(tools)

    finalizer_model = model.with_structured_output(
        InvestigationResponse, method="json_schema"
    )

    graph = StateGraph(State)

    # Add nodes
    graph.add_node(
        Nodes.TOOL,
        partial(tool_calls_node, tools={tool.get_name(): tool for tool in tools}),
    )
    graph.add_node(Nodes.LLM_CALL, partial(llm_call_node, model=agent_model))
    graph.add_node(
        Nodes.FINALIZER,
        partial(
            finalize_investigation_node,
            model=finalizer_model,
        ),
    )

    # Add edges
    graph.add_edge(START, Nodes.LLM_CALL)
    graph.add_conditional_edges(
        Nodes.LLM_CALL,
        should_continue,
        [Nodes.TOOL, Nodes.FINALIZER],
    )
    graph.add_edge(Nodes.TOOL, Nodes.LLM_CALL)
    graph.add_edge(Nodes.FINALIZER, END)

    agent = graph.compile()

    result = agent.invoke(
        {"messages": [HumanMessage(content="Investigate the incident INC-1042")]},
    )

    print(result)
