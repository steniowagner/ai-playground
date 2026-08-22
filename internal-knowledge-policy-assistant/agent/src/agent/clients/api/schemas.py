from agent.utils.default_values import DEFAULT_VALUES
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=DEFAULT_VALUES["top_k"], gt=0)
    min_score: float = Field(default=DEFAULT_VALUES["min_score"], ge=0.0)


class AskResponse(BaseModel):
    content: str
    sources: list[str]
