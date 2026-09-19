from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .after_finalize_investigation import after_finalize_investigation
    from .after_llm_call import after_llm_call
    from .after_scope_check import after_scope_check
    from .after_tool_call import after_tool_call

__all__ = [
    "after_finalize_investigation",
    "after_llm_call",
    "after_scope_check",
    "after_tool_call",
]

_EXPORTS = {
    "after_scope_check": (".after_scope_check", "after_scope_check"),
    "after_finalize_investigation": (
        ".after_finalize_investigation",
        "after_finalize_investigation",
    ),
    "after_llm_call": (".after_llm_call", "after_llm_call"),
    "after_tool_call": (".after_tool_call", "after_tool_call"),
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
