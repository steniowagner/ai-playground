from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .node import reject_out_of_scope_node


__all__ = ["reject_out_of_scope_node"]

_EXPORTS = {
    "reject_out_of_scope_node": (".node", "reject_out_of_scope_node"),
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
