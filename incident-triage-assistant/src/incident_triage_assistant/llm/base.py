from abc import ABC, abstractmethod
from typing import Any

from incident_triage_assistant.llm.schema import (
    LLMResponse,
    ToolCallResponse,
)
from incident_triage_assistant.tools.get_tools_definitions import (
    get_tools_definitions,
)


class LLMClient(ABC):
    def __init__(self) -> None:
        self._tools = get_tools_definitions()

    @abstractmethod
    def ask(self, question: str) -> LLMResponse:
        pass

    @abstractmethod
    def continue_with_tool_results(
        self, results: list[ToolCallResponse]
    ) -> LLMResponse:
        pass

    @abstractmethod
    def parse_tool_call_response(
        self, tool_call_id: str, tool_name: str, tool_response: Any
    ) -> ToolCallResponse:
        pass
