from sqlalchemy import select

from triage_ops.db import MaintenanceWindowsRecord, SessionFactory
from triage_ops.domain import MaintenanceWindow

from .base import MaintenanceWindowsRepository
from .schema import FindMaintenanceWindowsArgs


class PostgresMaintenanceWindowsRepository(MaintenanceWindowsRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def _parse_record(record: MaintenanceWindowsRecord) -> MaintenanceWindow:
        return MaintenanceWindow(
            maintenance_id=record.id,
            title=record.title,
            services=record.services,
            environment=record.environment,
            start_time=record.start_time,
            end_time=record.end_time,
            expected_effects=record.expected_effects,
            approved_by=record.approved_by,
            status=record.status,
        )

    def find(self, args: FindMaintenanceWindowsArgs) -> list[MaintenanceWindow]:
        statement = select(MaintenanceWindowsRecord).where(
            MaintenanceWindowsRecord.services.contains([args.service]),
            MaintenanceWindowsRecord.environment == args.environment,
            MaintenanceWindowsRecord.status != "cancelled",
            MaintenanceWindowsRecord.start_time < args.end_time,
            args.start_time < MaintenanceWindowsRecord.end_time,
        )

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]

    def find_all(self) -> list[MaintenanceWindow]:
        statement = select(MaintenanceWindowsRecord)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]
