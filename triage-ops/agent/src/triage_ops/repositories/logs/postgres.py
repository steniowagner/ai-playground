from sqlalchemy import select

from triage_ops.db import LogsRecord, SessionFactory
from triage_ops.repositories.logs import Log

from .base import LogsRepository
from .schema import FindLogsArgs


class PostgresLogsRepository(LogsRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def find(self, args: FindLogsArgs) -> list[Log]:
        statement = select(LogsRecord).where(
            LogsRecord.service == args.service,
            LogsRecord.environment == args.environment,
            LogsRecord.timestamp >= args.start_time,
            LogsRecord.timestamp <= args.end_time,
        )

        if args.contains:
            statement = statement.where(
                LogsRecord.message.contains(args.contains, autoescape=True)
            )

        if args.severity is not None:
            statement = statement.where(LogsRecord.severity.in_(sorted(args.severity)))

        statement = statement.order_by(LogsRecord.timestamp.asc()).limit(args.limit)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [
                Log(
                    log_id=record.id,
                    timestamp=record.timestamp,
                    service=record.service,
                    environment=record.environment,
                    severity=record.severity,
                    trace_id=record.trace_id,
                    message=record.message,
                    attributes=record.attributes,
                )
                for record in records
            ]
