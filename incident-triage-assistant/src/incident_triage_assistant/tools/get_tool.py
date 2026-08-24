from typing import Literal

from .get_incident.tool import get_incident

RegisteredTools = Literal["get_incident"]


def get_tool(tool: RegisteredTools):
    match tool:
        case "get_incident":
            return get_incident
        case _:
            raise ValueError(f'Tool "{tool}" not registered')
