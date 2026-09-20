from triage_ops.db.schema import SessionFactory
from triage_ops.repositories.logs import JSONLogsRepository, PostgresLogsRepository


def seed_logs(session_factory: SessionFactory) -> None:
    json_logs_repository = JSONLogsRepository()
    postgres_logs_repository = PostgresLogsRepository()

    logs = json_logs_repository.find()
