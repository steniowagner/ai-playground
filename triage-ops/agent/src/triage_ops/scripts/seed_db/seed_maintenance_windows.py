from logging import Logger

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import MaintenanceWindowsRecord, SessionFactory
from triage_ops.domain import MaintenanceWindow
from triage_ops.repositories.maintenance_windows import JSONMaintenanceWindowsRepository

from .exceptions import SeedDatabaseException


def save_maintenance_windows(
    session_factory: SessionFactory, maintenance_windows: list[MaintenanceWindow]
) -> None:
    records = [
        MaintenanceWindowsRecord(
            id=maintenance_window.maintenance_id,
            title=maintenance_window.title,
            services=maintenance_window.services,
            environment=maintenance_window.environment,
            start_time=maintenance_window.start_time,
            end_time=maintenance_window.end_time,
            expected_effects=maintenance_window.expected_effects,
            approved_by=maintenance_window.approved_by,
            status=maintenance_window.status,
        )
        for maintenance_window in maintenance_windows
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(MaintenanceWindowsRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException(
            "Failed to save maintenance-windows fixture data."
        ) from exc


def seed_maintenance_windows(session_factory: SessionFactory, logger: Logger) -> None:
    json_maintenance_window_repository = JSONMaintenanceWindowsRepository()
    maintenance_windows = json_maintenance_window_repository.find_all()
    save_maintenance_windows(session_factory, maintenance_windows)
    logger.warning("Maintenance Windows seeded ✓")
