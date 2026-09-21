from fastapi import Request
from triage_ops.evaluation.service import RunEvaluationCaseService
from triage_ops.repositories.evaluation_cases import EvaluationCasesRepository


def get_evaluation_cases_repository(request: Request) -> EvaluationCasesRepository:
    return request.app.state.evaluation_cases_repository


def get_run_evaluation_case_service(request: Request) -> RunEvaluationCaseService:
    return request.app.state.run_evaluation_case_service
