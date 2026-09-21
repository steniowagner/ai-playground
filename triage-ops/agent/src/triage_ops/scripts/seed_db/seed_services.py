from logging import Logger
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import ServicesRecord, SessionFactory
from triage_ops.domain import Service
from triage_ops.repositories.services import JSONServicesRepository

from .exceptions import SeedDatabaseException


def save_services(session_factory: SessionFactory, services: list[Service]) -> None:
    records = [
        ServicesRecord(
            id=uuid4(),
            service=service.service,
            display_name=service.display_name,
            description=service.description,
            tier=service.tier,
            owner_team=service.owner_team,
            on_call=service.on_call,
            environments=service.environments,
            dependencies=service.dependencies,
            runbook_ids=service.runbook_ids,
            slo=service.slo,
        )
        for service in services
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(ServicesRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException("Failed to save services fixture data.") from exc


def seed_services(session_factory: SessionFactory, logger: Logger) -> None:
    json_services_repository = JSONServicesRepository()
    services = json_services_repository.find_all()
    save_services(session_factory, services)
    logger.warning("Services seeded ✓")
