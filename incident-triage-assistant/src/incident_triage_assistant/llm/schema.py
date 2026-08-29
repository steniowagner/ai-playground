from typing import Literal

from pydantic import BaseModel, ConfigDict

LLMRole = Literal["system", "user", "assistant", "tool"]


class LLMToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    name: str
    args_str: str


class LLMQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: LLMRole
    content: str | None


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: LLMRole
    content: str | None
    tool_calls: list[LLMToolCall] | None
