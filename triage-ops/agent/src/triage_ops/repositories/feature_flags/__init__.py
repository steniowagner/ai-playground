from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import FeatureFlagsRepository
    from .json import JSONFeatureFlagsRepository
    from .postgres import PostgresFeatureFlagsRepository
    from .schema import FeatureFlag, FindFeatureFlagsArgs

__all__ = [
    "FeatureFlag",
    "FeatureFlagsRepository",
    "FindFeatureFlagsArgs",
    "JSONFeatureFlagsRepository",
    "PostgresFeatureFlagsRepository",
]

_EXPORTS = {
    "FeatureFlagsRepository": (".base", "FeatureFlagsRepository"),
    "JSONFeatureFlagsRepository": (".json", "JSONFeatureFlagsRepository"),
    "FindFeatureFlagsArgs": (".schema", "FindFeatureFlagsArgs"),
    "FeatureFlag": (".schema", "FeatureFlag"),
    "PostgresFeatureFlagsRepository": (".postgres", "PostgresFeatureFlagsRepository"),
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
