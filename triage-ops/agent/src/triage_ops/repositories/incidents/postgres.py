from sqlalchemy import select

from triage_ops.db import IncidentsRecord, SessionFactory
from triage_ops.repositories.incidents import Incident, IncidentAlert

from .base import IncidentRepository


class PostgresIncidentsRepository(IncidentRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def _parse_record(self, record: IncidentsRecord) -> Incident:
        return Incident(
            incident_id=record.id,
            title=record.title,
            environment=record.environment,
            primary_service=record.primary_service,
            alert_started_at=record.alert_started_at,
            created_at=record.created_at,
            status=record.status,
            severity=record.severity,
            reported_symptoms=record.reported_symptoms,
            alert=IncidentAlert.model_validate(record.alert),
        )

    def find_by_id(self, incident_id: str) -> Incident | None:
        with self._session_factory() as session:
            record = session.get(IncidentsRecord, incident_id)

            if record is None:
                return None

            return self._parse_record(record)

    def find_all(self) -> list[Incident]:
        statement = select(IncidentsRecord)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

            return [self._parse_record(record) for record in records]
