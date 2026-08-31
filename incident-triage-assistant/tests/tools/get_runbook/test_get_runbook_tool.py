from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.runbooks.base import RunbooksRepository
from incident_triage_assistant.tools.get_runbook.tool import GetRunbookTool
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def test_returns_repository_content() -> None:
    repository = Mock(spec=RunbooksRepository)
    repository.find_by_id.return_value = "# Checkout errors\nInvestigate dependencies."
    response = GetRunbookTool(repository)({"runbook_id": "RB-CHECKOUT-ERRORS"})
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.content.startswith("# Checkout errors")
    repository.find_by_id.assert_called_once_with("RB-CHECKOUT-ERRORS")


def test_returns_not_found_when_repository_has_no_runbook() -> None:
    repository = Mock(spec=RunbooksRepository)
    repository.find_by_id.return_value = None
    response = GetRunbookTool(repository)({"runbook_id": "RB-UNKNOWN"})
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "NOT_FOUND"


@pytest.mark.parametrize(
    "args", [{}, {"runbook_id": None}, {"runbook_id": "RB-1", "extra": True}]
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=RunbooksRepository)
    response = GetRunbookTool(repository)(args)
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find_by_id.assert_not_called()
