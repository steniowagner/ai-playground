from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .node import finalize_investigation_node

__all__ = [
    "finalize_investigation_node",
]

_EXPORTS = {
    "finalize_investigation_node": (".node", "finalize_investigation_node"),
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
