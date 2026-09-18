from pydantic import BaseModel, ConfigDict, Field


class GraphRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class GraphResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: str = Field(min_length=1)
    content: str
