from incident_triage_assistant.domain.types import Tool

from .schema import GetFeatureFlagsArgs

GET_FEATURE_FLAGS_TOOL: Tool = {
    "name": "get_feature_flags",
    "description": "Retrieve feature flags associated with an exact service and environment so the agent can determine whether a flag state or recent flag change may be related to an incident.",
    "parameters": GetFeatureFlagsArgs.model_json_schema(),
}
