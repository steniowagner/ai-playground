from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import ServicesRepository
    from .json import JSONServicesRepository
    from .postgres import PostgresServicesRepository
    from .schema import FindServiceArgs

__all__ = [
    "FindServiceArgs",
    "JSONServicesRepository",
    "PostgresServicesRepository",
    "ServicesRepository",
]

_EXPORTS = {
    "ServicesRepository": (".base", "ServicesRepository"),
    "JSONServicesRepository": (".json", "JSONServicesRepository"),
    "FindServiceArgs": (".schema", "FindServiceArgs"),
    "PostgresServicesRepository": (".postgres", "PostgresServicesRepository"),
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
