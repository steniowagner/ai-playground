from logging import Logger

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import MetricsRecord, SessionFactory
from triage_ops.domain import Metric
from triage_ops.repositories.metrics import JSONMetricsRepository

from .exceptions import SeedDatabaseException


def save_metrics(session_factory: SessionFactory, metrics: list[Metric]) -> None:
    records = [
        MetricsRecord(
            id=metric.metric_id,
            timestamp=metric.timestamp,
            service=metric.service,
            environment=metric.environment,
            values=metric.values.model_dump(),
        )
        for metric in metrics
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(MetricsRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException("Failed to save metrics fixture data.") from exc


def seed_metrics(session_factory: SessionFactory, logger: Logger) -> None:
    json_metrics_repository = JSONMetricsRepository()
    metrics = json_metrics_repository.find_all()
    save_metrics(session_factory, metrics)
    logger.warning("Metrics seeded ✓")
