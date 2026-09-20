from sqlalchemy import select

from triage_ops.db import FeatureFlagsRecord, SessionFactory

from .base import FeatureFlagsRepository
from .schema import FeatureFlag, FindFeatureFlagsArgs


class PostgresFeatureFlagsRepository(FeatureFlagsRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def find(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        statement = select(FeatureFlag).where(
            FeatureFlagsRecord.service == args.service,
            FeatureFlagsRecord.environment == args.environment,
        )

        if args.flag_name:
            statement = statement.where(FeatureFlagsRecord.flag == args.flag_name)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [
                FeatureFlag(
                    flag=record.flag,
                    service=record.service,
                    environment=record.environment,
                    enabled=record.enabled,
                    owner_team=record.owner_team,
                    changed_at=record.changed_at,
                    changed_by_deployment=record.changed_by_deployment,
                )
                for record in records
            ]
