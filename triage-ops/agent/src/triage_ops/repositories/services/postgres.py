from sqlalchemy import select

from triage_ops.db import ServicesRecord, SessionFactory
from triage_ops.domain import Service

from .base import ServicesRepository
from .schema import FindServiceArgs


class PostgresServicesRepository(ServicesRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def _parse_record(self, record: ServicesRecord) -> Service:
        return Service(
            service=record.service,
            display_name=record.service,
            description=record.description,
            tier=record.tier,
            owner_team=record.owner_team,
            on_call=record.on_call,
            environments=record.environments,
            dependencies=record.dependencies,
            runbook_ids=record.runbook_ids,
            slo=record.slo,
        )

    def find(self, args: FindServiceArgs) -> Service | None:
        statement = select(ServicesRecord).where(
            ServicesRecord.service == args.service,
            ServicesRecord.environments.contains([args.environment]),
        )

        with self._session_factory() as session:
            record = session.scalar(statement)

        if record is None:
            return None

        return self._parse_record(record)

    def find_all(self) -> list[Service]:
        statement = select(ServicesRecord)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]
