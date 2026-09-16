from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .bootstrap_services import (
        ServiceRegistry,
        bootstrap_services,
    )
    from .exceptions import ServiceExecutionException
    from .schema import (
        ServiceErrorResponse,
        ServiceErrorResponseDetail,
        ServiceResponse,
        ServiceSuccessResponse,
    )
    from .service import Service

__all__ = [
    "Service",
    "ServiceErrorResponse",
    "ServiceErrorResponseDetail",
    "ServiceExecutionException",
    "ServiceRegistry",
    "ServiceResponse",
    "ServiceSuccessResponse",
    "bootstrap_services",
]

_EXPORTS = {
    "ServiceRegistry": (".bootstrap_services", "ServiceRegistry"),
    "bootstrap_services": (".bootstrap_services", "bootstrap_services"),
    "ServiceExecutionException": (".exceptions", "ServiceExecutionException"),
    "ServiceErrorResponse": (".schema", "ServiceErrorResponse"),
    "ServiceErrorResponseDetail": (".schema", "ServiceErrorResponseDetail"),
    "ServiceResponse": (".schema", "ServiceResponse"),
    "ServiceSuccessResponse": (".schema", "ServiceSuccessResponse"),
    "Service": (".service", "Service"),
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
