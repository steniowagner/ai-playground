import json
from pathlib import Path
from typing import Any

import pytest
from incident_triage_assistant.tools.query_metrics.tool import query_metrics
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolSuccessResponse,
)


def write_metrics_file(path: Path, metrics: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(f"{json.dumps(metric)}\n" for metric in metrics),
        encoding="utf-8",
    )


def test_returns_requested_metric_series_filtered_and_sorted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_file = tmp_path / "metrics.jsonl"
    write_metrics_file(
        metrics_file,
        [
            {
                "metric_id": "metric-later",
                "timestamp": "2026-08-20T10:20:00Z",
                "service": "checkout-api",
                "environment": "production",
                "values": {"error_rate": 0.04, "request_rate": 120.0},
            },
            {
                "metric_id": "metric-other-service",
                "timestamp": "2026-08-20T10:15:00Z",
                "service": "web-gateway",
                "environment": "production",
                "values": {"error_rate": 0.9},
            },
            {
                "metric_id": "metric-earlier",
                "timestamp": "2026-08-20T10:10:00Z",
                "service": "checkout-api",
                "environment": "production",
                "values": {"error_rate": 0.0, "request_rate": 100.0},
            },
            {
                "metric_id": "metric-outside-window",
                "timestamp": "2026-08-20T09:59:00Z",
                "service": "checkout-api",
                "environment": "production",
                "values": {"error_rate": 0.8},
            },
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.tools.query_metrics.tool.METRICS_FILE",
        metrics_file,
    )

    response = query_metrics(
        {
            "service": "checkout-api",
            "environment": "production",
            "metric_names": ["error_rate", "request_rate"],
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.data.missing_metric_names == set()
    assert [point.metric_id for point in response.data.series["error_rate"]] == [
        "metric-earlier",
        "metric-later",
    ]
    assert [point.value for point in response.data.series["error_rate"]] == [
        0.0,
        0.04,
    ]
    assert [point.value for point in response.data.series["request_rate"]] == [
        100.0,
        120.0,
    ]


def test_reports_requested_metric_with_no_values_as_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_file = tmp_path / "metrics.jsonl"
    write_metrics_file(
        metrics_file,
        [
            {
                "metric_id": "metric-001",
                "timestamp": "2026-08-20T10:10:00Z",
                "service": "checkout-api",
                "environment": "production",
                "values": {"error_rate": 0.02},
            }
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.tools.query_metrics.tool.METRICS_FILE",
        metrics_file,
    )

    response = query_metrics(
        {
            "service": "checkout-api",
            "environment": "production",
            "metric_names": ["error_rate", "queue_depth"],
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.data.missing_metric_names == {"queue_depth"}
    assert response.data.series["queue_depth"] == []


@pytest.mark.parametrize(
    "invalid_args",
    [
        {
            "service": "checkout-api",
            "environment": "production",
            "metric_names": [],
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "metric_names": ["unknown_metric"],
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "metric_names": ["error_rate"],
            "start_time": "2026-08-20T10:30:00Z",
            "end_time": "2026-08-20T10:00:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "metric_names": ["error_rate"],
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T11:01:00Z",
        },
        {
            "service": "checkout-api",
            "environment": "production",
            "metric_names": ["error_rate"],
            "start_time": "2026-08-20T10:00:00",
            "end_time": "2026-08-20T10:30:00",
        },
    ],
)
def test_returns_invalid_argument_for_invalid_input(
    invalid_args: dict[str, Any],
) -> None:
    response = query_metrics(invalid_args)

    assert isinstance(response, ToolErrorResponse)
    assert response.ok is False
    assert response.error.code == "INVALID_ARGUMENT"
    assert response.error.message.strip()
