import os

from langchain_anthropic import ChatAnthropic


def create_anthropic_model(model_name: str | None = None) -> ChatAnthropic:
    return ChatAnthropic(
        model=model_name or os.environ["ANTHROPIC_MODEL"],
        timeout=None,
        stop=None,
        thinking={"type": "enabled", "budget_tokens": 5000},
    )
