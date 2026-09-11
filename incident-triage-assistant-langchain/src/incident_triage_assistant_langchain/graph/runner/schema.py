from typing import Any, Literal, TypeAlias

from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationOutcome,
)
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict

GraphInput: TypeAlias = dict[str, Any] | Command


class GraphRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "running",
        "completed",
        "awaiting_approval",
    ] = "running"
    final_result: InvestigationOutcome | None = None
    approval_request: dict | None = None
