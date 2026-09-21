from collections.abc import Mapping
from pathlib import Path

from pydantic import ValidationError

from triage_ops.evaluation.schema import EvaluationCase

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import EvaluationCasesRepository, EvaluationSplit

EVALUATION_DATASETS_DIRECTORY = Path(__file__).resolve().parents[4] / "data" / "evals"

DEFAULT_DATASET_PATHS: dict[EvaluationSplit, Path] = {
    "development": EVALUATION_DATASETS_DIRECTORY / "development.jsonl",
    "held_out": EVALUATION_DATASETS_DIRECTORY / "held_out.jsonl",
}


class JSONLEvaluationCasesRepository(EvaluationCasesRepository):
    def __init__(
        self,
        dataset_paths: Mapping[EvaluationSplit, Path] | None = None,
    ) -> None:
        self._dataset_paths = dict(dataset_paths or DEFAULT_DATASET_PATHS)

    def _read_lines(self, path: Path) -> list[str]:
        try:
            return path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Evaluation-case repository contains invalid text data."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable(
                "Evaluation-case repository is unavailable."
            ) from exc

    def _load_cases(self, path: Path) -> list[EvaluationCase]:
        cases: list[EvaluationCase] = []
        case_ids: set[str] = set()

        for line_number, line in enumerate(self._read_lines(path), 1):
            if not line.strip():
                continue

            try:
                case = EvaluationCase.model_validate_json(line)
            except ValidationError as exc:
                raise RepositoryDataError(
                    f"Invalid evaluation case at {path}:{line_number}."
                ) from exc

            if case.case_id in case_ids:
                raise RepositoryDataError(
                    f"Duplicate evaluation case ID: {case.case_id}."
                )

            case_ids.add(case.case_id)
            cases.append(case)

        return cases

    def find_all(self, split: EvaluationSplit) -> list[EvaluationCase]:
        return self._load_cases(self._dataset_paths[split])

    def find_by_id(self, case_id: str) -> EvaluationCase | None:
        if case_id.startswith("dev-"):
            split: EvaluationSplit = "development"
        elif case_id.startswith("holdout-"):
            split = "held_out"
        else:
            return None

        return next(
            (case for case in self.find_all(split) if case.case_id == case_id),
            None,
        )
