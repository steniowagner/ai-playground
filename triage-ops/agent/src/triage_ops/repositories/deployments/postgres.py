from sqlalchemy import select

from triage_ops.db import DeploymentsRecord, SessionFactory
from triage_ops.domain import Deployment

from .base import DeploymentsRepository
from .schema import FindDeploymentsArgs


class PostgresDeploymentsRepository(DeploymentsRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def find(self, args: FindDeploymentsArgs) -> list[Deployment]:
        statement = select(DeploymentsRecord).where(
            DeploymentsRecord.service == args.service,
            DeploymentsRecord.environment == args.environment,
            DeploymentsRecord.started_at <= args.completed_at,
            args.started_at <= DeploymentsRecord.completed_at,
        )

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [
                Deployment(
                    deployment_id=record.id,
                    service=record.service,
                    environment=record.environment,
                    version=record.version,
                    commit=record.commit,
                    started_at=record.started_at,
                    completed_at=record.completed_at,
                    status=record.status,
                    summary=record.summary,
                )
                for record in records
            ]
