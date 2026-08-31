import json
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.metrics.json import JSONMetricsRepository
from incident_triage_assistant.repositories.metrics.schema import FindMetricsArgs


def metric(
    identifier: str, timestamp: str, service: str = "checkout-api"
) -> dict[str, object]:
    return {
        "metric_id": identifier,
        "timestamp": timestamp,
        "service": service,
        "environment": "production",
        "values": {"error_rate": 0.04},
    }


def test_filters_by_context_and_time_then_sorts_oldest_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "metrics.jsonl"
    rows = [
        metric("later", "2026-08-20T10:20:00Z"),
        metric("other", "2026-08-20T10:15:00Z", "catalog-api"),
        metric("earlier", "2026-08-20T10:10:00Z"),
        metric("outside", "2026-08-20T09:59:00Z"),
    ]
    path.write_text("".join(f"{json.dumps(item)}\n" for item in rows), encoding="utf-8")
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.metrics.json.METRICS_FILE", path
    )
    args = FindMetricsArgs(
        service="checkout-api",
        environment="production",
        metric_names={"error_rate"},
        start_time="2026-08-20T10:00:00Z",
        end_time="2026-08-20T10:30:00Z",
    )
    assert [item.metric_id for item in JSONMetricsRepository().find(args)] == [
        "earlier",
        "later",
    ]


def test_ignores_blank_jsonl_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "metrics.jsonl"
    path.write_text(
        f"\n{json.dumps(metric('one', '2026-08-20T10:10:00Z'))}\n\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.metrics.json.METRICS_FILE", path
    )
    args = FindMetricsArgs(
        service="checkout-api",
        environment="production",
        metric_names={"error_rate"},
        start_time="2026-08-20T10:00:00Z",
        end_time="2026-08-20T10:30:00Z",
    )
    assert [item.metric_id for item in JSONMetricsRepository().find(args)] == ["one"]
