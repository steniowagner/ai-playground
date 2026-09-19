import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import SampleQuestionsRepository
from .schema import SampleQuestions, SampleQuestionsFixture

SAMPLE_QUESTIONS_FILE = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "sample_questions"
    / "sample_questions.json"
)


class JSONSampleQuestionsRepository(SampleQuestionsRepository):
    def _parse_fixture(self, fixture_json: Any) -> SampleQuestionsFixture:
        try:
            return SampleQuestionsFixture.model_validate(fixture_json)
        except ValidationError as exc:
            raise RepositoryDataError(
                "Sample-questions repository data is invalid"
            ) from exc

    def _read_sample_questions(self) -> SampleQuestionsFixture:
        try:
            with open(SAMPLE_QUESTIONS_FILE, "r", encoding="utf-8") as f:
                sample_questions_json = json.load(f)
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Sample-questions repository contains invalid text data."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RepositoryDataError(
                "Sample-questions repository contains invalid JSON."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable(
                "Sample-questions repository is unavailable."
            ) from exc

        return self._parse_fixture(sample_questions_json)

    def find_all(self) -> SampleQuestions:
        sample_questions_fixture = self._read_sample_questions()
        return SampleQuestions.model_validate(
            sample_questions_fixture.model_dump(exclude={"schema_version"})
        )
