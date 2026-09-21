from sqlalchemy import select

from triage_ops.db import MetricsRecord, SessionFactory
from triage_ops.domain import Metric, MetricValues

from .base import MetricsRepository
from .schema import FindMetricsArgs


class PostgresMetricsRepository(MetricsRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def _parse_record(self, record: MetricsRecord) -> Metric:
        return Metric(
            metric_id=record.id,
            timestamp=record.timestamp,
            service=record.service,
            environment=record.environment,
            values=MetricValues.model_validate(record.values),
        )

    def find(self, args: FindMetricsArgs) -> list[Metric]:
        statement = select(MetricsRecord).where(
            MetricsRecord.service == args.service,
            MetricsRecord.environment == args.environment,
            args.start_time <= MetricsRecord.timestamp,
            MetricsRecord.timestamp <= args.end_time,
        )

        statement = statement.order_by(MetricsRecord.timestamp.asc())

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]

    def find_all(self) -> list[Metric]:
        statement = select(MetricsRecord)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]
