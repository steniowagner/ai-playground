from incident_triage_assistant.tools.types import Tool

from .schema import GetFeatureFlagsArgs

GET_FEATURE_FLAGS_TOOL = Tool(
    name="get_feature_flags",
    description="Retrieve feature flags for one exact service and environment, optionally filtered by an exact flag name. Use flag state and change metadata as investigation evidence, but do not treat timing alone as proof of causation or claim that this read-only tool changed a flag.",
    parameters=GetFeatureFlagsArgs.model_json_schema(),
)
