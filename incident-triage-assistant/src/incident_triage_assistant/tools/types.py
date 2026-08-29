from collections.abc import Callable
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict


class Tool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str
    parameters: dict[str, Any]


ToolErrorResponseCode = Literal[
    "NOT_FOUND",
    "INVALID_ARGUMENT",
    "UNKNOWN_TOOL",
    "EXECUTION_ERROR",
]


class ToolErrorResponseDetail(BaseModel):
    code: ToolErrorResponseCode
    message: str


class ToolErrorResponse(BaseModel):
    ok: Literal[False]
    data: None = None
    error: ToolErrorResponseDetail


T = TypeVar("T")


class ToolSuccessResponse(BaseModel, Generic[T]):
    ok: Literal[True]
    data: T
    error: None = None


ToolResponse = ToolSuccessResponse[T] | ToolErrorResponse


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["tool"] = "tool"
    tool_call_id: str
    name: str
    content: str


ToolHandler = Callable[[dict[str, Any]], ToolResponse]


class ToolRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    definition: Tool
    handler: ToolHandler
