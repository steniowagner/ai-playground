from logging import Logger

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import LogsRecord
from triage_ops.db.schema import SessionFactory
from triage_ops.domain import Log
from triage_ops.repositories.logs import JSONLogsRepository

from .exceptions import SeedDatabaseException


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
    json_logs_repository = JSONLogsRepository()
    logs = json_logs_repository.find_all()
    save_logs(session_factory, logs)
    logger.warning("Logs seeded ✓")
