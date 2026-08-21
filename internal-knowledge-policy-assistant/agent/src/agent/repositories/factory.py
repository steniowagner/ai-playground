from typing import Literal

from .base import VectorRepository
from .in_memory import InMemoryVectorRepository


def create_repository(repository: Literal["in-memory"]) -> VectorRepository:
    match repository:
        case "in-memory":
            return InMemoryVectorRepository()
        case _:
            raise ValueError(f"Repository {repository} not supported")
