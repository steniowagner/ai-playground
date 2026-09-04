from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ToolErrorResponseCode = Literal[
    "NOT_FOUND",
    "INVALID_ARGUMENT",
    "UNKNOWN_TOOL",
    "EXECUTION_ERROR",
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
