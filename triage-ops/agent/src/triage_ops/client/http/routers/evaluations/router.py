from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from triage_ops.evaluation.behavioral import BehavioralCaseResult
from triage_ops.evaluation.exceptions import EvaluationCaseNotFoundError
from triage_ops.evaluation.schema import EvaluationCase
from triage_ops.evaluation.service import RunEvaluationCaseService
from triage_ops.repositories.evaluation_cases import (
    EvaluationCasesRepository,
    EvaluationSplit,
)

from .dependencies import (
    get_evaluation_cases_repository,
    get_run_evaluation_case_service,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

EvaluationCasesDependency = Annotated[
    EvaluationCasesRepository,
    Depends(get_evaluation_cases_repository),
]

RunEvaluationCaseDependency = Annotated[
    RunEvaluationCaseService,
    Depends(get_run_evaluation_case_service),
]


@router.get("/")
def list_evaluation_cases(
    cases_repository: EvaluationCasesDependency,
    split: EvaluationSplit = "development",
) -> list[EvaluationCase]:
    return cases_repository.find_all(split)


@router.post("/{case_id}/run")
async def run_evaluation_case(
    case_id: str,
    service: RunEvaluationCaseDependency,
    confirm_held_out: bool = False,
) -> BehavioralCaseResult:
    if case_id.startswith("holdout-") and not confirm_held_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Held-out evaluation requires confirm_held_out=true and must not be used for prompt tuning.",
        )

    try:
        return await service.execute(case_id)
    except EvaluationCaseNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
