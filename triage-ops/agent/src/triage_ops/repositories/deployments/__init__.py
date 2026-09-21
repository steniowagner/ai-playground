from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import DeploymentsRepository
    from .json import JSONDeploymentsRepository
    from .postgres import PostgresDeploymentsRepository
    from .schema import FindDeploymentsArgs

__all__ = [
    "DeploymentsRepository",
    "FindDeploymentsArgs",
    "JSONDeploymentsRepository",
    "PostgresDeploymentsRepository",
]

_EXPORTS = {
    "DeploymentsRepository": (".base", "DeploymentsRepository"),
    "JSONDeploymentsRepository": (".json", "JSONDeploymentsRepository"),
    "FindDeploymentsArgs": (".schema", "FindDeploymentsArgs"),
    "PostgresDeploymentsRepository": (".postgres", "PostgresDeploymentsRepository"),
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
