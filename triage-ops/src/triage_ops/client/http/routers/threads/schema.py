from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateThreadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: UUID


class StartThreadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    message: str = Field(min_length=1)
