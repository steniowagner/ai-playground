from logging import Logger

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import DeploymentsRecord, SessionFactory
from triage_ops.domain import Deployment
from triage_ops.repositories.deployments import JSONDeploymentsRepository

from .exceptions import SeedDatabaseException


def save_deployments(
    session_factory: SessionFactory, deployments: list[Deployment]
) -> None:
    records = [
        DeploymentsRecord(
            id=deployment.deployment_id,
            service=deployment.service,
            environment=deployment.environment,
            version=deployment.version,
            commit=deployment.commit,
            started_at=deployment.started_at,
            completed_at=deployment.completed_at,
            status=deployment.status,
            summary=deployment.summary,
        )
        for deployment in deployments
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(DeploymentsRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException("Failed to save deployments fixture data.") from exc


def seed_deployments(session_factory: SessionFactory, logger: Logger) -> None:
    json_deployments_repository = JSONDeploymentsRepository()
    deployments = json_deployments_repository.find_all()
    save_deployments(session_factory, deployments)
    logger.warning("Deployments seeded ✓")
