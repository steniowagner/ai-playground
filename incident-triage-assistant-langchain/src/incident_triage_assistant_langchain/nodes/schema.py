from enum import Enum


class Nodes(str, Enum):
    TOOL = "tool_calls_node"
    LLM_CALL = "llm_call_node"
