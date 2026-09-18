from fastapi import Request
from triage_ops.repositories.sample_questions.base import SampleQuestionsRepository


def get_sample_questions_repository(request: Request) -> SampleQuestionsRepository:
    return request.app.state.sample_questions_repository
