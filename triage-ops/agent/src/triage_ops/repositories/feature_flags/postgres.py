from sqlalchemy import select

from triage_ops.db import FeatureFlagsRecord, SessionFactory
from triage_ops.domain import FeatureFlag

from .base import FeatureFlagsRepository
from .schema import FindFeatureFlagsArgs


class PostgresFeatureFlagsRepository(FeatureFlagsRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def _parse_record(self, record: FeatureFlagsRecord) -> FeatureFlag:
        return FeatureFlag(
            flag=record.flag,
            service=record.service,
            environment=record.environment,
            enabled=record.enabled,
            owner_team=record.owner_team,
            changed_at=record.changed_at,
            changed_by_deployment=record.changed_by_deployment,
        )

    def find_all(self) -> list[FeatureFlag]:
        statement = select(FeatureFlagsRecord)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]

    def find(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        statement = select(FeatureFlagsRecord).where(
            FeatureFlagsRecord.service == args.service,
            FeatureFlagsRecord.environment == args.environment,
        )

        if args.flag_name:
            statement = statement.where(FeatureFlagsRecord.flag == args.flag_name)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]
