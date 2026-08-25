class AgentIterationLimitError(Exception):
    def __init__(self):
        message = "Max number of agent iterations reached."
        super().__init__(message)
        self._message = message

    def __str__(self):
        return self._message


class EmptyLLMReturn(Exception):
    def __init__(self):
        message = "LLM returned neither tool calls nor content."
        super().__init__(message)
        self._message = message

    def __str__(self):
        return self._message
