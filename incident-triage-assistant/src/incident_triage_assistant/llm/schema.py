from typing import Literal

from pydantic import BaseModel, ConfigDict

LLMRole = Literal["system", "user", "assistant", "tool"]


class LLMToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    name: str
    serialized_arguments: str


class LLMQuestion(BaseModel):
    role: LLMRole
    content: str | None


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: LLMRole
    content: str | None
    tool_calls: list[LLMToolCall] | None


class ToolCallResponse(BaseModel):
    role: Literal["tool"] = "tool"
    tool_call_id: str
    name: str
    content: str
