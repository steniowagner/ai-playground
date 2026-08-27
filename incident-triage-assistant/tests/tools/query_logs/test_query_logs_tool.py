import json
from pathlib import Path
from typing import Any

import pytest
from incident_triage_assistant.tools.query_logs.tool import query_logs
from incident_triage_assistant.tools.tool_response import (
    ToolErrorResponse,
    ToolSuccessResponse,
)


def write_logs_file(path: Path, logs: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(f"{json.dumps(log)}\n" for log in logs),
        encoding="utf-8",
    )


def test_returns_logs_filtered_by_context_and_sorted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logs_file = tmp_path / "logs.jsonl"
    write_logs_file(
        logs_file,
        [
            {
                "log_id": "log-later",
                "timestamp": "2026-08-20T10:20:00Z",
                "service": "checkout-api",
                "environment": "production",
                "severity": "ERROR",
                "trace_id": "trace-002",
                "message": "Payment request timed out",
                "attributes": {"http_status": 504},
            },
            {
                "log_id": "log-other-service",
                "timestamp": "2026-08-20T10:15:00Z",
                "service": "web-gateway",
                "environment": "production",
                "severity": "ERROR",
                "trace_id": "trace-003",
                "message": "Upstream request failed",
                "attributes": {"http_status": 502},
            },
            {
                "log_id": "log-earlier",
                "timestamp": "2026-08-20T10:10:00Z",
                "service": "checkout-api",
                "environment": "production",
                "severity": "WARN",
                "trace_id": "trace-001",
                "message": "Payment request exceeded latency budget",
                "attributes": {"duration_ms": 4200},
            },
            {
                "log_id": "log-outside-window",
                "timestamp": "2026-08-20T09:59:00Z",
                "service": "checkout-api",
                "environment": "production",
                "severity": "ERROR",
                "trace_id": None,
                "message": "Old payment failure",
                "attributes": {},
            },
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.tools.query_logs.tool.LOGS_FILE",
        logs_file,
    )

    response = query_logs(
        {
            "service": "checkout-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert [log.log_id for log in response.data.logs] == [
        "log-earlier",
        "log-later",
    ]


def test_applies_contains_severity_and_limit_filters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logs_file = tmp_path / "logs.jsonl"
    write_logs_file(
        logs_file,
        [
            {
                "log_id": "log-003",
                "timestamp": "2026-08-20T10:12:00Z",
                "service": "checkout-api",
                "environment": "production",
                "severity": "WARN",
                "trace_id": None,
                "message": "Payment request timed out",
                "attributes": {},
            },
            {
                "log_id": "log-002",
                "timestamp": "2026-08-20T10:11:00Z",
                "service": "checkout-api",
                "environment": "production",
                "severity": "ERROR",
                "trace_id": None,
                "message": "Inventory request timed out",
                "attributes": {},
            },
            {
                "log_id": "log-001",
                "timestamp": "2026-08-20T10:10:00Z",
                "service": "checkout-api",
                "environment": "production",
                "severity": "ERROR",
                "trace_id": None,
                "message": "Payment request timed out",
                "attributes": {},
            },
            {
                "log_id": "log-004",
                "timestamp": "2026-08-20T10:13:00Z",
                "service": "checkout-api",
                "environment": "production",
                "severity": "ERROR",
                "trace_id": None,
                "message": "Payment authorization timed out",
                "attributes": {},
            },
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.tools.query_logs.tool.LOGS_FILE",
        logs_file,
    )

    response = query_logs(
        {
            "service": "checkout-api",
            "environment": "production",
            "contains": "Payment",
            "severity": ["ERROR"],
            "limit": 1,
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert [log.log_id for log in response.data.logs] == ["log-001"]


@pytest.mark.parametrize(
    "invalid_args",
    [
        {
            "service": "checkout-api",
            "environment": "production",
            "severity": [],
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "severity": ["DEBUG"],
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "limit": 0,
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "limit": 51,
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "start_time": "2026-08-20T10:30:00Z",
            "end_time": "2026-08-20T10:00:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T11:01:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00",
            "end_time": "2026-08-20T10:30:00",
        },
    ],
)
def test_returns_invalid_argument_for_invalid_input(
    invalid_args: dict[str, Any],
) -> None:
    response = query_logs(invalid_args)

    assert isinstance(response, ToolErrorResponse)
    assert response.ok is False
    assert response.error.code == "INVALID_ARGUMENT"
    assert response.error.message.strip()
