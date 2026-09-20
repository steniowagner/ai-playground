from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import IncidentRepository
    from .json import JSONIncidentRepository
    from .postgres import PostgresIncidentsRepository
    from .schema import Incident, IncidentAlert

__all__ = [
    "Incident",
    "IncidentAlert",
    "IncidentRepository",
    "JSONIncidentRepository",
    "PostgresIncidentsRepository",
]

_EXPORTS = {
    "IncidentRepository": (".base", "IncidentRepository"),
    "JSONIncidentRepository": (".json", "JSONIncidentRepository"),
    "PostgresIncidentsRepository": (".postgres", "PostgresIncidentsRepository"),
    "Incident": (".schema", "Incident"),
    "IncidentAlert": (".schema", "IncidentAlert"),
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
