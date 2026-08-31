import json
from pathlib import Path
from typing import Any

import pytest
from incident_triage_assistant.repositories.feature_flags.json import JSONFeatureFlagsRepository
from incident_triage_assistant.tools.get_feature_flags.tool import GetFeatureFlagsTool
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

repository = JSONFeatureFlagsRepository()
get_feature_flags = GetFeatureFlagsTool(repository)


def read_feature_flags():
    return repository._read_feature_flags()


def write_feature_flags_file(
    path: Path,
    feature_flags: list[dict[str, Any]],
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "feature_flags": feature_flags,
            }
        ),
        encoding="utf-8",
    )


def feature_flag(
    flag: str,
    service: str = "checkout-api",
    environment: str = "production",
) -> dict[str, Any]:
    return {
        "flag": flag,
        "service": service,
        "environment": environment,
        "enabled": True,
        "owner_team": "payments",
        "changed_at": "2026-08-20T10:00:00Z",
        "changed_by_deployment": "dep-test-001",
    }


def test_returns_service_flags_sorted_by_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    feature_flags_file = tmp_path / "feature_flags.json"
    write_feature_flags_file(
        feature_flags_file,
        [
            feature_flag("checkout_tax_validation"),
            feature_flag("gateway_rate_limit", service="web-gateway"),
            feature_flag("checkout_address_validation"),
            feature_flag(
                "checkout_staging_only",
                environment="staging",
            ),
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.feature_flags.json.FEATURE_FLAGS_FILE",
        feature_flags_file,
    )

    response = get_feature_flags(
        {
            "service": "checkout-api",
            "environment": "production",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert [flag.flag for flag in response.data.feature_flags] == [
        "checkout_address_validation",
        "checkout_tax_validation",
    ]


def test_filters_by_exact_flag_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    feature_flags_file = tmp_path / "feature_flags.json"
    write_feature_flags_file(
        feature_flags_file,
        [
            feature_flag("checkout_address_validation"),
            feature_flag("checkout_tax_validation"),
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.feature_flags.json.FEATURE_FLAGS_FILE",
        feature_flags_file,
    )

    response = get_feature_flags(
        {
            "service": "checkout-api",
            "environment": "production",
            "flag_name": "checkout_tax_validation",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert [flag.flag for flag in response.data.feature_flags] == [
        "checkout_tax_validation"
    ]


def test_returns_empty_success_when_no_flags_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    feature_flags_file = tmp_path / "feature_flags.json"
    write_feature_flags_file(feature_flags_file, [])
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.feature_flags.json.FEATURE_FLAGS_FILE",
        feature_flags_file,
    )

    response = get_feature_flags(
        {
            "service": "checkout-api",
            "environment": "production",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.data.feature_flags == []


def test_rejects_invalid_fixture_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    feature_flags_file = tmp_path / "feature_flags.json"
    feature_flags_file.write_text(
        json.dumps(
            {
                "schema_version": "2.0",
                "feature_flags": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.feature_flags.json.FEATURE_FLAGS_FILE",
        feature_flags_file,
    )

    with pytest.raises(ValidationError):
        read_feature_flags()


@pytest.mark.parametrize(
    "invalid_args",
    [
        {},
        {
            "service": "checkout-api",
            "environment": "unknown",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "flag_name": "",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "extra": True,
        },
    ],
)
def test_returns_invalid_argument_for_invalid_input(
    invalid_args: dict[str, Any],
) -> None:
    response = get_feature_flags(invalid_args)

    assert isinstance(response, ToolErrorResponse)
    assert response.ok is False
    assert response.error.code == "INVALID_ARGUMENT"
    assert response.error.message.strip()
