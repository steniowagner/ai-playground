from logging import Logger
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import FeatureFlagsRecord, SessionFactory
from triage_ops.domain import (
    FeatureFlag,
)
from triage_ops.repositories.feature_flags import JSONFeatureFlagsRepository

from .exceptions import SeedDatabaseException


def save_feature_flags(
    session_factory: SessionFactory, feature_flags: list[FeatureFlag]
) -> None:
    records = [
        FeatureFlagsRecord(
            id=uuid4(),
            flag=feature_flag.flag,
            service=feature_flag.service,
            environment=feature_flag.environment,
            enabled=feature_flag.enabled,
            owner_team=feature_flag.owner_team,
            changed_at=feature_flag.changed_at,
            changed_by_deployment=feature_flag.changed_by_deployment,
        )
        for feature_flag in feature_flags
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(FeatureFlagsRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException("Failed to save incident fixture data.") from exc


def seed_feature_flags(session_factory: SessionFactory, logger: Logger) -> None:
    json_feature_flags_repository = JSONFeatureFlagsRepository()
    feature_flags = json_feature_flags_repository.find_all()
    save_feature_flags(session_factory, feature_flags)
    logger.warning("Feature-flags seeded ✓")
