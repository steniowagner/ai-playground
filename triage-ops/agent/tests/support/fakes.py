from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any

from triage_ops.domain.investigation import InvestigationResponse
from triage_ops.graph.nodes.check_scope import ScopeDecision
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

    def _respond(self, argument: Any) -> Any:
        self.calls.append(argument)
        if self.error is not None:
            raise self.error
        return self.result

    def find(self, args: Any) -> Any:
        return self._respond(args)

    def find_by_id(self, identifier: Any) -> Any:
        return self._respond(identifier)


class RecordingService:
    """Service double that records mutations and returns a configurable result."""

    def __init__(self, result: Any | None = None, error: Exception | None = None):
        self.result = (
            ServiceSuccessResponse(ok=True, data={}) if result is None else result
        )
        self.error = error
        self.calls: list[Any] = []

    def execute(self, args: Any) -> Any:
        self.calls.append(args)
        if self.error is not None:
            raise self.error
        return self.result


class RecordingStreamWriter:
    """Callable stream writer that retains emitted payloads in order."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def __call__(self, event: dict[str, Any]) -> None:
        self.events.append(event)


class ScriptedGraphModel:
    """Graph-compatible model double with independent response queues."""

    def __init__(
        self,
        *,
        scopes: Iterable[ScopeDecision],
        agent_messages: Iterable[Any],
        final_responses: Iterable[InvestigationResponse] = (),
    ) -> None:
        self.scope = ScriptedModel(scopes)
        self.agent = ScriptedModel(agent_messages)
        self.finalizer = ScriptedModel(final_responses)

    def bind_tools(self, _tools: list[Any]) -> ScriptedModel:
        return self.agent

    def with_structured_output(
        self, schema: type[Any], **_kwargs: Any
    ) -> ScriptedModel:
        if schema is ScopeDecision:
            return self.scope
        if schema is InvestigationResponse:
            return self.finalizer
        raise AssertionError(f"Unexpected structured schema: {schema}")
