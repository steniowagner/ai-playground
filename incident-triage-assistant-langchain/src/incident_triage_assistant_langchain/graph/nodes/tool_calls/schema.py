from enum import Enum


class ToolCallStreamEventCodes(str, Enum):
    INCIDENT_ID_NOT_PROVIDED = "incident_id_not_provided"
    REPEATED_TOOL_CALL = "repeated_tool_call"
    UNKNOWN_TOOL = "unknown_tool"
    INVALID_ARGUMENTS = "invalid_arguments"
