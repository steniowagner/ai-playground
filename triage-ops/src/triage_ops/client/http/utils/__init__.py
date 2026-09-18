from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .create_graph_runner import create_graph_runner
    from .create_thread_id import create_thread_id
    from .get_graph_runner import get_graph_runner

__all__ = ["create_graph_runner", "create_thread_id", "get_graph_runner"]

_EXPORTS = {
    "create_thread_id": (".create_thread_id", "create_thread_id"),
    "get_graph_runner": (".get_graph_runner", "get_graph_runner"),
    "create_graph_runner": (".create_graph_runner", "create_graph_runner"),
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
