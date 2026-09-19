from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .node import check_scope_node
    from .schema import RequestScope, ScopeDecision

__all__ = ["RequestScope", "ScopeDecision", "check_scope_node"]

_EXPORTS = {
    "RequestScope": (".schema", "RequestScope"),
    "ScopeDecision": (".schema", "ScopeDecision"),
    "check_scope_node": (".node", "check_scope_node"),
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
