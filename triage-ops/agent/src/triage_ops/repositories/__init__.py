from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .exceptions import (
        RepositoryDataError,
        RepositoryException,
        RepositoryUnavailable,
    )

__all__ = [
    "RepositoryDataError",
    "RepositoryException",
    "RepositoryUnavailable",
]

_EXPORTS = {
    "RepositoryDataError": (".exceptions", "RepositoryDataError"),
    "RepositoryException": (".exceptions", "RepositoryException"),
    "RepositoryUnavailable": (".exceptions", "RepositoryUnavailable"),
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
