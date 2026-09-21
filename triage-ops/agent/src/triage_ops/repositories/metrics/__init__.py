from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import MetricsRepository
    from .json import JSONMetricsRepository
    from .postgres import PostgresMetricsRepository
    from .schema import FindMetricsArgs

__all__ = [
    "FindMetricsArgs",
    "JSONMetricsRepository",
    "MetricsRepository",
    "PostgresMetricsRepository",
]

_EXPORTS = {
    "MetricsRepository": (".base", "MetricsRepository"),
    "JSONMetricsRepository": (".json", "JSONMetricsRepository"),
    "FindMetricsArgs": (".schema", "FindMetricsArgs"),
    "PostgresMetricsRepository": (".postgres", "PostgresMetricsRepository"),
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
