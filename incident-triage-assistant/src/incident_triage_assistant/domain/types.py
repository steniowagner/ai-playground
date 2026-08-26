from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

IncidentStatus = Literal["investigating", "monitoring", "resolved"]

Environment = Literal["production", "staging"]


class Tool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str
    args: dict[str, Any]
