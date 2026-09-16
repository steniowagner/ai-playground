from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Checkpointer

from triage_ops.domain.investigation.schema import (
    InvestigationResponse,
)
from triage_ops.graph.conditions.after_finalize_investigation import (
    after_finalize_investigation,
)
from triage_ops.graph.conditions.after_llm_call import (
    after_llm_call,
)
from triage_ops.graph.conditions.after_tool_call import (
    after_tool_call,
)
from triage_ops.graph.nodes.execute_approvals.node import (
    execute_approvals_node,
)
from triage_ops.graph.nodes.finalize_investigation.node import (
    finalize_investigation_node,
)
from triage_ops.graph.nodes.llm_call.node import llm_call_node
from triage_ops.graph.nodes.prepare_approvals.node import (
    prepare_approvals_node,
)
from triage_ops.graph.nodes.prepare_user_request.node import (
    prepare_user_request_node,
)
from triage_ops.graph.nodes.request_approvals.node import (
    request_approvals_node,
)
from triage_ops.graph.nodes.schema import Nodes
from triage_ops.graph.nodes.tool_calls.node import (
    tool_calls_node,
)
from triage_ops.model.schema import Model
from triage_ops.services.bootstrap_services import (
    bootstrap_services,
)
from triage_ops.tools.bootstrap_tools import bootstrap_tools

from .state import State


def build_graph(model: Model, checkpointer: Checkpointer) -> CompiledStateGraph:
    tools = bootstrap_tools()
    service_registry = bootstrap_services()

    agent_model = model.bind_tools(tools)
    finalizer_model = model.with_structured_output(
        InvestigationResponse, method="json_schema"
    )

    graph = StateGraph(State)

    graph.add_node(Nodes.PREPARE_USER_REQUEST, prepare_user_request_node)
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

    graph.add_edge(START, Nodes.PREPARE_USER_REQUEST)
    graph.add_edge(Nodes.PREPARE_USER_REQUEST, Nodes.LLM_CALL)
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

    return graph.compile(checkpointer=checkpointer)
