from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import EvaluationCasesRepository, EvaluationSplit
    from .json import JSONLEvaluationCasesRepository

__all__ = [
    "EvaluationCasesRepository",
    "EvaluationSplit",
    "JSONLEvaluationCasesRepository",
]

_EXPORTS = {
    "EvaluationCasesRepository": (".base", "EvaluationCasesRepository"),
    "EvaluationSplit": (".base", "EvaluationSplit"),
    "JSONLEvaluationCasesRepository": (
        ".json",
        "JSONLEvaluationCasesRepository",
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
