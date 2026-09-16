import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Literal, TypedDict, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ServiceErrorResponseCode = Literal[
    "INVALID_ARGUMENT",
    "UNKNOWN_TOOL",
    "EXECUTION_ERROR",
]

T = TypeVar("T")


class ServiceErrorResponseDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ServiceErrorResponseCode
    message: str
    input: dict[str, Any] = Field(default_factory=dict)


class ServiceErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[False]
    data: None = None
    error: ServiceErrorResponseDetail


class ServiceSuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[True]
    data: T
    error: None = None


type ServiceResponse[ResponseT] = (
    ServiceSuccessResponse[ResponseT] | ServiceErrorResponse
)


class Service[Args](ABC):
    def __init__(self):
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def execute(self, args: Args) -> ServiceResponse:
        pass


class ServiceRegistry(TypedDict):
    rollback_deployment: Service
    disable_feature_flag: Service
    restart_service: Service
    escalate_incident: Service
