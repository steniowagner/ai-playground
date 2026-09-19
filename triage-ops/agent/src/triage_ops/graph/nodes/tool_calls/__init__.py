from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .node import tool_calls_node
    from .utils import find_messages_since_last_human_message

__all__ = [
    "find_messages_since_last_human_message",
    "tool_calls_node",
]

_EXPORTS = {
    "tool_calls_node": (".node", "tool_calls_node"),
    "find_messages_since_last_human_message": (
        ".utils",
        "find_messages_since_last_human_message",
    ),
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
