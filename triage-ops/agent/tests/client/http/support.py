from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from triage_ops.evaluation.behavioral import BehavioralCaseResult
from triage_ops.evaluation.exceptions import EvaluationCaseNotFoundError
from triage_ops.evaluation.schema import EvaluationCase
from triage_ops.graph.event_stream import GraphEvent
from triage_ops.graph.nodes.request_approvals import ApprovalDecision
from triage_ops.repositories.evaluation_cases import EvaluationSplit
from triage_ops.repositories.sample_questions import SampleQuestions


class RecordingGraphRunner:
    def __init__(self) -> None:
        self.start_events: list[GraphEvent] = []
        self.resume_events: list[GraphEvent] = []
        self.start_calls: list[tuple[str, str]] = []
        self.resume_calls: list[tuple[str, list[ApprovalDecision]]] = []

    async def start(self, thread_id: str, message: str) -> AsyncIterator[GraphEvent]:
        self.start_calls.append((thread_id, message))
        for event in self.start_events:
            yield event

    async def resume(
        self, thread_id: str, decisions: list[ApprovalDecision]
    ) -> AsyncIterator[GraphEvent]:
        self.resume_calls.append((thread_id, decisions))
        for event in self.resume_events:
            yield event


class RecordingSampleQuestionsRepository:
    def __init__(self, result: SampleQuestions) -> None:
        self.result = result
        self.calls = 0

    def find_all(self) -> SampleQuestions:
        self.calls += 1
        return self.result


class RecordingEvaluationCasesRepository:
    def __init__(self, cases: list[EvaluationCase]) -> None:
        self.cases = cases
        self.find_all_calls: list[EvaluationSplit] = []

    def find_all(self, split: EvaluationSplit) -> list[EvaluationCase]:
        self.find_all_calls.append(split)
        return [case for case in self.cases if case.split == split]


class RecordingRunEvaluationCaseService:
    def __init__(self, result: BehavioralCaseResult) -> None:
        self.result = result
        self.case_ids: list[str] = []
        self.missing_case_ids: set[str] = set()

    async def execute(self, case_id: str) -> BehavioralCaseResult:
        self.case_ids.append(case_id)
        if case_id in self.missing_case_ids:
            raise EvaluationCaseNotFoundError(case_id)
        return self.result


def parse_sse_events(response_text: str) -> list[dict[str, Any]]:
    normalized = response_text.replace("\r\n", "\n")
    records = [record for record in normalized.split("\n\n") if record.strip()]
    events: list[dict[str, Any]] = []

    for record in records:
        fields: dict[str, str] = {}
        for line in record.splitlines():
            if not line or line.startswith(":"):
                continue
            name, _, value = line.partition(":")
            fields[name] = value.removeprefix(" ")

        events.append(
            {
                "id": fields.get("id"),
                "event": fields.get("event"),
                "data": json.loads(fields["data"]),
            }
        )

    return events
