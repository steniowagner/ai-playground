from dataclasses import dataclass

from langchain_core.tools import BaseTool
from langgraph.types import Checkpointer

from triage_ops.model import Model


@dataclass(frozen=True)
class BuildGraphArgs:
    model: Model
    checkpointer: Checkpointer
    tools: list[BaseTool]
