from typing import Any

from pydantic import BaseModel, ConfigDict

from .get_incident.definition import GET_INCIDENT_TOOL

tools_definitions = [GET_INCIDENT_TOOL]


class ToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str
    parameters: dict[str, Any]


def get_tools_definitions() -> list[ToolDefinition]:
    return [
        ToolDefinition.model_validate(tool_definition)
        for tool_definition in tools_definitions
    ]
