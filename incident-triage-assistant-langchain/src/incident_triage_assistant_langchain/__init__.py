from functools import partial

from dotenv import load_dotenv
from langchain.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

from incident_triage_assistant_langchain.conditions.should_continue import (
    should_continue,
)
from incident_triage_assistant_langchain.nodes.llm_call import llm_call_node
from incident_triage_assistant_langchain.nodes.schema import Nodes
from incident_triage_assistant_langchain.nodes.tool_calls import tool_calls_node

from .state import State
from .tools.bootstrap_tools import bootstrap_tools


def main() -> None:
    load_dotenv()

    model = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
    )

    tools = bootstrap_tools()
    mapping_tools = {tool.get_name(): tool for tool in tools}
    model_with_tools = model.bind_tools(tools)

    graph = StateGraph(State)

    # Add nodes
    graph.add_node(Nodes.TOOL, partial(tool_calls_node, tools=mapping_tools))
    graph.add_node(
        Nodes.LLM_CALL, partial(llm_call_node, model_with_tools=model_with_tools)
    )

    # Add edges
    graph.add_edge(START, Nodes.LLM_CALL)
    graph.add_conditional_edges(Nodes.LLM_CALL, should_continue, [Nodes.TOOL, END])
    graph.add_edge(Nodes.TOOL, Nodes.LLM_CALL)

    agent = graph.compile()

    messages = [HumanMessage(content="Investigate the incident INC-1042")]
    messages = agent.invoke({"messages": messages})

    for message in messages["messages"]:
        print(message.pretty_repr())
