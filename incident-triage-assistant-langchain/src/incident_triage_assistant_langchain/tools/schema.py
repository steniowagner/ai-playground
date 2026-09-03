from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

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
