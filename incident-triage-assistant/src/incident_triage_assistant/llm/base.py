from abc import ABC, abstractmethod
from typing import Any

from incident_triage_assistant.llm.schema import (
    LLMResponse,
)
from incident_triage_assistant.tools.types import ToolCallResponse


class LLMClient(ABC):
    @abstractmethod
    def ask(self, question: str) -> LLMResponse:
        pass

    @abstractmethod
    def continue_with_tool_results(
        self, results: list[ToolCallResponse]
    ) -> LLMResponse:
        pass

    @abstractmethod
    def continue_after_invalid_result(
        self,
        validation_feedback: str,
    ) -> LLMResponse:
        pass

    @abstractmethod
    def parse_tool_call_response(
        self, tool_call_id: str, tool_name: str, tool_response: Any
    ) -> ToolCallResponse:
        pass
