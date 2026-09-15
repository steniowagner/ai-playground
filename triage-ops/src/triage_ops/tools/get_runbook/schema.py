from pydantic import BaseModel, ConfigDict


class GetRunbookArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runbook_id: str


class GetRunbookResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runbook_id: str
    content: str
