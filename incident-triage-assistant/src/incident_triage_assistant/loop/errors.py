class AgentIterationLimitError(Exception):
    def __init__(self):
        super().__init__("Max number of agent iterations reached.")


class EmptyLLMReturn(Exception):
    def __init__(self):
        super().__init__("LLM returned neither tool-calls nor content.")


class InvalidInvestigationResultError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "The language model repeatedly returned an invalid or incomplete investigation result."
        )
