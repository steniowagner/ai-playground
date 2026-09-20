from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models.feature_flags import FeatureFlagsRecord
    from .models.incidents import IncidentsRecord
    from .models.logs import LogsRecord
    from .schema import (
        SessionFactory,
    )
    from .utils import create_database_engine, create_session_factory

__all__ = [
    "FeatureFlagsRecord",
    "IncidentsRecord",
    "LogsRecord",
    "SessionFactory",
    "create_database_engine",
    "create_session_factory",
]

_EXPORTS = {
    "SessionFactory": (".schema", "SessionFactory"),
    "create_database_engine": (".utils", "create_database_engine"),
    "create_session_factory": (".utils", "create_session_factory"),
    "LogsRecord": (".models.logs", "LogsRecord"),
    "IncidentsRecord": (".models.incidents", "IncidentsRecord"),
    "FeatureFlagsRecord": (".models.incidents", "FeatureFlagsRecord"),
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
