from enum import Enum


class StreamEvents(str, Enum):
    TOOL_STARTED = "tool_started"
    TOOL_SKIPPED = "tool_skipped"
    TOOL_FAIELD = "tool_failed"
    TOOL_FINISHED = "tool_finished"
