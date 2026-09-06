from typing import Annotated

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationFailure,
    InvestigationResult,
)


class State(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    final_result: InvestigationResult | InvestigationFailure | None = None
