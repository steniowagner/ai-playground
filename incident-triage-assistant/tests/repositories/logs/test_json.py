import json
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.logs.json import JSONLogsRepository
from incident_triage_assistant.repositories.logs.schema import FindLogsArgs


def log(
    identifier: str,
    timestamp: str,
    severity: str = "ERROR",
    message: str = "Payment failed",
    service: str = "checkout-api",
) -> dict[str, object]:
    return {
        "log_id": identifier,
        "timestamp": timestamp,
        "service": service,
        "environment": "production",
        "severity": severity,
        "trace_id": None,
        "message": message,
        "attributes": {},
    }


def write_logs(path: Path, logs: list[dict[str, object]]) -> None:
    path.write_text("".join(f"{json.dumps(item)}\n" for item in logs), encoding="utf-8")


def test_applies_context_optional_filters_order_and_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "logs.jsonl"
    write_logs(
        path,
        [
            log("later", "2026-08-20T10:20:00Z"),
            log("earlier", "2026-08-20T10:10:00Z"),
            log("wrong-severity", "2026-08-20T10:05:00Z", "INFO"),
            log("wrong-message", "2026-08-20T10:06:00Z", message="Inventory failed"),
            log("wrong-service", "2026-08-20T10:07:00Z", service="catalog-api"),
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.logs.json.LOGS_FILE", path
    )
    args = FindLogsArgs(
        service="checkout-api",
        environment="production",
        contains="Payment",
        severity={"ERROR"},
        limit=1,
        start_time="2026-08-20T10:00:00Z",
        end_time="2026-08-20T10:30:00Z",
    )
    result = JSONLogsRepository().find(args)
    assert [item.log_id for item in result] == ["earlier"]


def test_none_severity_includes_all_severities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "logs.jsonl"
    write_logs(
        path,
        [
            log("error", "2026-08-20T10:10:00Z"),
            log("info", "2026-08-20T10:11:00Z", "INFO"),
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.logs.json.LOGS_FILE", path
    )
    args = FindLogsArgs(
        service="checkout-api",
        environment="production",
        contains=None,
        severity=None,
        limit=50,
        start_time="2026-08-20T10:00:00Z",
        end_time="2026-08-20T10:30:00Z",
    )
    assert [item.log_id for item in JSONLogsRepository().find(args)] == [
        "error",
        "info",
    ]
