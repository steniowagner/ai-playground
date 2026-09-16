from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any

from triage_ops.services import ServiceSuccessResponse


class ScriptedModel:
    """Small model double that returns queued responses and records every input."""

    def __init__(self, responses: Iterable[Any]) -> None:
        self._responses = deque(responses)
        self.inputs: list[Any] = []

    def invoke(self, model_input: Any, *_args: Any, **_kwargs: Any) -> Any:
        self.inputs.append(model_input)
        if not self._responses:
            raise AssertionError("The scripted model has no response left.")
        response = self._responses.popleft()
        if isinstance(response, Exception):
            raise response
        return response

    @property
    def remaining_responses(self) -> int:
        return len(self._responses)


class RecordingRepository:
    """Configurable repository double for tool and repository-contract tests."""

    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[Any] = []

    def find(self, args: Any) -> Any:
        self.calls.append(args)
        if self.error is not None:
            raise self.error
        return self.result


class RecordingService:
    """Service double that records mutations and returns a configurable result."""

    def __init__(self, result: Any | None = None, error: Exception | None = None):
        self.result = result or ServiceSuccessResponse(ok=True, data={})
        self.error = error
        self.calls: list[Any] = []

    def execute(self, args: Any) -> Any:
        self.calls.append(args)
        if self.error is not None:
            raise self.error
        return self.result
