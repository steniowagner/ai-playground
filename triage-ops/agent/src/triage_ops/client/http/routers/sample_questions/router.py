from typing import Annotated

from fastapi import APIRouter, Depends
from triage_ops.repositories.sample_questions import (
    SampleQuestions,
    SampleQuestionsRepository,
)

from .dependencies import get_sample_questions_repository

router = APIRouter(prefix="/sample-questions", tags=["sample-questions"])


SampleQuestionsDependency = Annotated[
    SampleQuestionsRepository, Depends(get_sample_questions_repository)
]


@router.get("/")
def sample_questions(
    sample_questions_repository: SampleQuestionsDependency,
) -> SampleQuestions:
    return sample_questions_repository.find_all()
