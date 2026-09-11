from dataclasses import dataclass
from enum import Enum

from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationOutcome,
)


@dataclass
class StreamUpdate:
    final_result: InvestigationOutcome | None = None
    approval_request: dict | None = None


class StreamEvents(str, Enum):
    TOOL_STARTED = "tool_started"
    TOOL_SKIPPED = "tool_skipped"
    TOOL_FAILED = "tool_failed"
    TOOL_FINISHED = "tool_finished"
