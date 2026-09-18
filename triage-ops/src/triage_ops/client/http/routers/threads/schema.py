from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateThreadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: UUID
