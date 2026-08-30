from pathlib import Path
from typing import Any

from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import Log, QueryLogsArgs, QueryLogsResult

LOGS_FILE = Path(__file__).resolve().parents[4] / "data" / "fixtures" / "logs.jsonl"


def read_logs() -> list[Log]:
    logs = []

    with open(LOGS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                log = Log.model_validate_json(line)
                logs.append(log)

    return logs


def filter_by_message_content(args: QueryLogsArgs, logs: list[Log]) -> list[Log]:
    if not args.contains:
        return logs

    return [log for log in logs if args.contains in log.message]


def filter_by_severity(args: QueryLogsArgs, logs: list[Log]) -> list[Log]:
    if args.severity is None:
        return logs

    return [log for log in logs if log.severity in args.severity]


def filter_by_optional_filters(args: QueryLogsArgs, logs: list[Log]) -> list[Log]:
    filtered_logs = filter_by_message_content(args, logs)
    filtered_logs = filter_by_severity(args, filtered_logs)
    sorted_logs = sorted(filtered_logs, key=lambda log: log.timestamp)

    return sorted_logs


def filter_logs(args: QueryLogsArgs, all_logs: list[Log]) -> list[Log]:
    logs = [
        log
        for log in all_logs
        if log.service == args.service
        and log.environment == args.environment
        and args.start_time <= log.timestamp
        and log.timestamp <= args.end_time
    ]

    return filter_by_optional_filters(args, logs)


def query_logs(raw_args: dict[str, Any]) -> ToolResponse[QueryLogsResult]:
    try:
        args = QueryLogsArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
            ),
        )

    all_logs = read_logs()
    filtered_logs = filter_logs(args, all_logs)[: args.limit]

    return ToolSuccessResponse(ok=True, data=QueryLogsResult(logs=filtered_logs))
