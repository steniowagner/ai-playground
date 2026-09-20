import json
from logging import Logger
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import MaintenanceWindowsRecord, SessionFactory
from triage_ops.domain import MaintenanceWindow
from triage_ops.repositories.maintenance_windows import MaintenanceWindowsFixture

from .exceptions import SeedDatabaseException

MAINTENANCE_WINDOWS_FILE = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "fixtures"
    / "maintenance_windows.json"
)


def parse_fixture(fixture_json: Any) -> MaintenanceWindowsFixture:
    try:
        return MaintenanceWindowsFixture.model_validate(fixture_json)
    except ValidationError as exc:
        raise SeedDatabaseException(
            "Maintenance-windows repository data is invalid."
        ) from exc


def read_maintenance_windows() -> list[MaintenanceWindow]:
    try:
        with open(MAINTENANCE_WINDOWS_FILE, "r", encoding="utf-8") as f:
            maintenance_windows_json = json.load(f)
    except json.JSONDecodeError as exc:
        raise SeedDatabaseException(
            "Maintenance-windows repository contains invalid JSON."
        ) from exc
    except UnicodeDecodeError as exc:
        raise SeedDatabaseException(
            "Maintenance-windows repository contains invalid text data."
        ) from exc
    except OSError as exc:
        raise SeedDatabaseException(
            "Maintenance-windows repository is unavailable."
        ) from exc

    fixture = parse_fixture(maintenance_windows_json)
    return fixture.maintenance_windows


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
    maintenance_windows = read_maintenance_windows()
    save_maintenance_windows(session_factory, maintenance_windows)
    logger.warning("Maintenance Windows seeded ✓")
