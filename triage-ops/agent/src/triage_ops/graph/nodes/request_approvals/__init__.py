from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .exceptions import InvalidApprovalResponse
    from .node import request_approvals_node
    from .schema import ApprovalDecision

__all__ = [
    "ApprovalDecision",
    "InvalidApprovalResponse",
    "request_approvals_node",
]

_EXPORTS = {
    "InvalidApprovalResponse": (".exceptions", "InvalidApprovalResponse"),
    "request_approvals_node": (".node", "request_approvals_node"),
    "ApprovalDecision": (".schema", "ApprovalDecision"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as error:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from error

    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value
