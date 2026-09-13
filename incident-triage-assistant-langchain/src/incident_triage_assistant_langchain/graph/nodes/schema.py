from enum import Enum


class Nodes(str, Enum):
    PREPARE_USER_REQUEST = "prepare_user_request_node"
    TOOL = "tool_calls_node"
    LLM_CALL = "llm_call_node"
    FINALIZER = "finalize_investigation_node"
    PREPARE_APPROVALS = "prepare_approvals_node"
    REQUEST_APPROVALS = "request_approvals_node"
    EXECUTE_APPROVALS = "execute_approvals_node"
