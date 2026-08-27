from incident_triage_assistant.domain.types import Tool

from .schema import GetRunbookArgs

GET_RUNBOOK_TOOL: Tool = {
    "name": "get_runbook",
    "description": "Retrieve the complete contents of an operational runbook by its runbook ID.",
    "parameters": GetRunbookArgs.model_json_schema(),
}
