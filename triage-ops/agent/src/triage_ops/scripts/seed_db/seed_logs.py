from logging import Logger
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import LogsRecord
from triage_ops.db.schema import SessionFactory
from triage_ops.repositories.logs import Log

from .exceptions import SeedDatabaseException

LOGS_FILE = Path(__file__).resolve().parents[4] / "data" / "fixtures" / "logs.jsonl"


def parse_fixture(fixture_str: str) -> Log:
    try:
        return Log.model_validate_json(fixture_str)
    except ValidationError as exc:
        raise SeedDatabaseException("Log source data is invalid.") from exc


def read_logs_from_fixture() -> list[Log]:
    logs: list[Log] = []

    try:
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    log = parse_fixture(line)
                    logs.append(log)
    except UnicodeDecodeError as exc:
        raise SeedDatabaseException("Logs source contains invalid text data.") from exc
    except OSError as exc:
        raise SeedDatabaseException("Logs source is unavailable.") from exc

    return logs


def save_logs(session_factory: SessionFactory, logs: list[Log]) -> None:
    records = [
        LogsRecord(
            id=log.log_id,
            timestamp=log.timestamp,
            service=log.service,
            environment=log.environment,
            severity=log.severity,
            trace_id=log.trace_id,
            message=log.message,
            attributes=log.attributes,
        )
        for log in logs
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(LogsRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException("Failed to save log fixture data.") from exc


def seed_logs(session_factory: SessionFactory, logger: Logger) -> None:
    logs = read_logs_from_fixture()
    save_logs(session_factory, logs)
    logger.warning("Logs seeded ✓")
