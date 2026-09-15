import os

from langchain_anthropic import ChatAnthropic


def create_anthropic_model() -> ChatAnthropic:
    return ChatAnthropic(
        model=os.environ["ANTHROPIC_MODEL"],
        timeout=None,
        stop=None,
        thinking={"type": "enabled", "budget_tokens": 5000},
    )
