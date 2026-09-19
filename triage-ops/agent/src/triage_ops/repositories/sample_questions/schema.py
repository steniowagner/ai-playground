from typing import Literal

from pydantic import BaseModel, ConfigDict


class SampleQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    category: str
    question: str
    expected_answer: str
    tags: list[str]


class SampleQuestions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    description: str
    questions: list[SampleQuestion]


class SampleQuestionsFixture(SampleQuestions):
    schema_version: Literal["1.0"]
