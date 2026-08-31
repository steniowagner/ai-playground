from pathlib import Path
from typing import Any

import pytest
from incident_triage_assistant.repositories.runbooks.json import JSONRunbooksRepository
from incident_triage_assistant.tools.get_runbook.tool import GetRunbookTool
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolSuccessResponse,
)

get_runbook = GetRunbookTool(JSONRunbooksRepository())


def test_returns_complete_runbook_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_content = """# Checkout Errors

1. Check the error rate.
2. Inspect recent deployments.
3. Request approval before rollback.
"""
    (tmp_path / "RB-CHECKOUT-ERRORS.md").write_text(
        expected_content,
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.runbooks.json.RUNBOOKS_DIR",
        tmp_path,
    )

    response = get_runbook({"runbook_id": "RB-CHECKOUT-ERRORS"})

    assert isinstance(response, ToolSuccessResponse)
    assert response.data.runbook_id == "RB-CHECKOUT-ERRORS"
    assert response.data.content == expected_content


def test_returns_not_found_for_unknown_runbook(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.runbooks.json.RUNBOOKS_DIR",
        tmp_path,
    )

    response = get_runbook({"runbook_id": "RB-UNKNOWN"})

    assert isinstance(response, ToolErrorResponse)
    assert response.ok is False
    assert response.error.code == "NOT_FOUND"
    assert "RB-UNKNOWN" in response.error.message


def test_ignores_non_markdown_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "RB-NOT-A-RUNBOOK.txt").write_text(
        "This is not a runbook.",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.runbooks.json.RUNBOOKS_DIR",
        tmp_path,
    )

    response = get_runbook({"runbook_id": "RB-NOT-A-RUNBOOK"})

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "NOT_FOUND"


@pytest.mark.parametrize(
    "invalid_args",
    [
        {},
        {"runbook_id": "RB-CHECKOUT-ERRORS", "extra": True},
        {"runbook_id": None},
    ],
)
def test_returns_invalid_argument_for_invalid_input(
    invalid_args: dict[str, Any],
) -> None:
    response = get_runbook(invalid_args)

    assert isinstance(response, ToolErrorResponse)
    assert response.ok is False
    assert response.error.code == "INVALID_ARGUMENT"
    assert response.error.message.strip()
