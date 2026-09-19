from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class RequestScope(StrEnum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"


class ScopeDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: RequestScope
