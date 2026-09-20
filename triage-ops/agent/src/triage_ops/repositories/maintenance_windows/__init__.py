from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import MaintenanceWindowsRepository
    from .json import JSONMaintenanceWindowsRepository
    from .postgres import PostgresMaintenanceWindowsRepository
    from .schema import FindMaintenanceWindowsArgs

__all__ = [
    "FindMaintenanceWindowsArgs",
    "JSONMaintenanceWindowsRepository",
    "MaintenanceWindowsRepository",
    "PostgresMaintenanceWindowsRepository",
]

_EXPORTS = {
    "MaintenanceWindowsRepository": (".base", "MaintenanceWindowsRepository"),
    "JSONMaintenanceWindowsRepository": (".json", "JSONMaintenanceWindowsRepository"),
    "FindMaintenanceWindowsArgs": (".schema", "FindMaintenanceWindowsArgs"),
    "PostgresMaintenanceWindowsRepository": (
        ".postgres",
        "PostgresMaintenanceWindowsRepository",
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
