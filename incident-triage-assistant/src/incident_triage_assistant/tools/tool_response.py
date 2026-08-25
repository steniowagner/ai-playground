from typing import Any, Literal

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


class ToolResponseSuccess(BaseModel):
    ok: Literal[True]
    data: dict[str, Any]
    error: None = None


ToolResponse = ToolResponseSuccess | ToolErrorResponse
