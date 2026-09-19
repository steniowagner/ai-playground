from langchain_core.tools import BaseTool
from pydantic import BaseModel

from triage_ops.tools import (
    ToolResponse,
    ToolSuccessResponse,
)

from ..schema import ToolNames
from .schema import (
    CompleteInvestigationArgs,
    CompleteInvestigationResult,
    CompletionReason,
)


class CompleteInvestigationTool(BaseTool):
    """
    Control-flow signal, not an operational tool.

    It performs no work. Calling it is how the model declares that a requested
    full investigation is finished, which routes the graph to the finalizer.
    Routing on an explicit tool call keeps the decision structured and
    validated instead of parsed out of free-form assistant prose.
    """

    name: str = ToolNames.COMPLETE_INVESTIGATION
    description: str = (
        "Signal that evidence collection for a requested full incident "
        "investigation is finished and the structured report should now be "
        "produced by a separate finalizer. Call this only after get_incident "
        "succeeded and no further tool call would materially improve the "
        "conclusion, or after the incident lookup failed conclusively. Never "
        "call it for greetings, definitions, clarifying questions, or single "
        "resource lookups."
    )
    args_schema: type[BaseModel] = CompleteInvestigationArgs

    def _run(
        self, incident_id: str, reason: CompletionReason
    ) -> ToolResponse[CompleteInvestigationResult]:
        CompleteInvestigationArgs(incident_id=incident_id, reason=reason)

        return ToolSuccessResponse(ok=True, data=CompleteInvestigationResult())
