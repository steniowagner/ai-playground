from pathlib import Path

import pytest
from incident_triage_assistant.repositories.runbooks.json import JSONRunbooksRepository


def test_returns_complete_markdown_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "RB-CHECKOUT.md").write_text(
        "# Checkout\nFollow the evidence.", encoding="utf-8"
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.runbooks.json.RUNBOOKS_DIR", tmp_path
    )
    assert (
        JSONRunbooksRepository().find_by_id("RB-CHECKOUT")
        == "# Checkout\nFollow the evidence."
    )


def test_ignores_non_markdown_files_and_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "RB-SECRET.txt").write_text("not a runbook", encoding="utf-8")
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.runbooks.json.RUNBOOKS_DIR", tmp_path
    )
    assert JSONRunbooksRepository().find_by_id("RB-SECRET") is None
