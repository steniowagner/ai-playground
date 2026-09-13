from enum import StrEnum
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ToolNames(StrEnum):
    COMPLETE_INVESTIGATION = "complete_investigation"
    GET_INCIDENT = "get_incident"
    GET_FEATURE_FLAGS = "get_feature_flags"
    GET_MAINTENANCE_WINDOWS = "get_maintenance_windows"
    GET_RECENT_DEPLOYMENTS = "get_recent_deployments"
    GET_RUNBOOK = "get_runbook"
    GET_SERVICE_CONTEXT = "get_service_context"
    QUERY_LOGS = "query_logs"
    QUERY_METRICS = "query_metrics"


ToolErrorResponseCode = Literal[
    "NOT_FOUND",
    "INVALID_ARGUMENT",
    "UNKNOWN_TOOL",
    "EXECUTION_ERROR",
    "RETRY_NOT_ALLOWED",
]


class ToolErrorResponseDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ToolErrorResponseCode
    message: str
    retryable: bool = False
    input: dict[str, Any] = Field(default_factory=dict)
    suggested_action: str | None = None


class ToolErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[False]
    data: None = None
    error: ToolErrorResponseDetail


T = TypeVar("T")


class ToolSuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[True]
    data: T
    error: None = None


type ToolResponse[ResponseT] = ToolSuccessResponse[ResponseT] | ToolErrorResponse
