import json
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.feature_flags.json import (
    JSONFeatureFlagsRepository,
)
from incident_triage_assistant.repositories.feature_flags.schema import (
    FindFeatureFlagsArgs,
)
from pydantic import ValidationError


def flag(
    name: str, service: str = "checkout-api", environment: str = "production"
) -> dict[str, object]:
    return {
        "flag": name,
        "service": service,
        "environment": environment,
        "enabled": True,
        "owner_team": "payments",
        "changed_at": "2026-08-20T10:00:00Z",
        "changed_by_deployment": "dep-1",
    }


def write_fixture(path: Path, flags: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps({"schema_version": "1.0", "feature_flags": flags}), encoding="utf-8"
    )


def test_filters_and_sorts_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "flags.json"
    write_fixture(path, [flag("z_flag"), flag("other", "catalog-api"), flag("a_flag")])
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.feature_flags.json.FEATURE_FLAGS_FILE",
        path,
    )
    result = JSONFeatureFlagsRepository().find(
        FindFeatureFlagsArgs(service="checkout-api", environment="production")
    )
    assert [item.flag for item in result] == ["a_flag", "z_flag"]


def test_filters_by_exact_flag_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "flags.json"
    write_fixture(path, [flag("a_flag"), flag("z_flag")])
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.feature_flags.json.FEATURE_FLAGS_FILE",
        path,
    )
    result = JSONFeatureFlagsRepository().find(
        FindFeatureFlagsArgs(
            service="checkout-api", environment="production", flag_name="z_flag"
        )
    )
    assert [item.flag for item in result] == ["z_flag"]


def test_rejects_invalid_schema_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "flags.json"
    path.write_text(
        json.dumps({"schema_version": "2.0", "feature_flags": []}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.feature_flags.json.FEATURE_FLAGS_FILE",
        path,
    )
    with pytest.raises(ValidationError):
        JSONFeatureFlagsRepository().find(
            FindFeatureFlagsArgs(service="checkout-api", environment="production")
        )
