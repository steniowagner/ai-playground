import pytest
from agent.repositories.factory import create_repository
from agent.repositories.in_memory import InMemoryVectorRepository


def test_create_in_memory_repository() -> None:
    repository = create_repository("in-memory")

    assert isinstance(repository, InMemoryVectorRepository)


def test_unsupported_repository_is_rejected() -> None:
    with pytest.raises(ValueError, match="Repository persistent not supported"):
        create_repository("persistent")  # type: ignore[arg-type]
