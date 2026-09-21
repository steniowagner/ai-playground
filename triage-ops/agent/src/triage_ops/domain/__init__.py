from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .deployment import Deployment
    from .feature_flag import FeatureFlag
    from .log import Log, LogSeverity
    from .maintenance_window import MaintenanceWindow
    from .metrics import Metric, MetricValues, ServiceMetric
    from .service import Service
    from .types import (
        Environment,
        IncidentSeverity,
    )

__all__ = [
    "Deployment",
    "Environment",
    "FeatureFlag",
    "IncidentSeverity",
    "Log",
    "LogSeverity",
    "MaintenanceWindow",
    "Metric",
    "MetricValues",
    "Service",
    "ServiceMetric",
]

_EXPORTS = {
    "Environment": (".types", "Environment"),
    "FeatureFlag": (".feature_flag", "FeatureFlag"),
    "IncidentSeverity": (".types", "IncidentSeverity"),
    "MaintenanceWindow": (".maintenance_window", "MaintenanceWindow"),
    "Deployment": (".deployment", "Deployment"),
    "Log": (".log", "Log"),
    "LogSeverity": (".log", "LogSeverity"),
    "Service": (".service", "Service"),
    "Metric": (".metrics", "Metric"),
    "ServiceMetric": (".metrics", "ServiceMetric"),
    "MetricValues": (".metrics", "MetricValues"),
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
