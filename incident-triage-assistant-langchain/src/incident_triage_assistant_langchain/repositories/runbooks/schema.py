from pydantic import BaseModel, ConfigDict


class FindRunbookByIdArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runbook_id: str
