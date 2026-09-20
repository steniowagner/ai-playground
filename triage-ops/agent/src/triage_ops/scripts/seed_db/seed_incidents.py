from logging import Logger
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import IncidentsRecord, SessionFactory
from triage_ops.repositories.incidents import Incident, JSONIncidentRepository

from .exceptions import SeedDatabaseException

INCIDENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "incidents.json"
)


def save_incidents(session_factory: SessionFactory, incidents: list[Incident]) -> None:
    records = [
        IncidentsRecord(
            id=incident.incident_id,
            title=incident.title,
            environment=incident.environment,
            primary_service=incident.primary_service,
            alert_started_at=incident.alert_started_at,
            created_at=incident.created_at,
            status=incident.status,
            severity=incident.severity,
            reported_symptoms=incident.reported_symptoms,
            alert=incident.alert.model_dump(),
        )
        for incident in incidents
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(IncidentsRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException("Failed to save incident fixture data.") from exc


def seed_incidents(session_factory: SessionFactory, logger: Logger) -> None:
    json_incident_repository = JSONIncidentRepository()
    incidents = json_incident_repository.find()
    save_incidents(session_factory, incidents)
    logger.warning("Incidents seeded ✓")
