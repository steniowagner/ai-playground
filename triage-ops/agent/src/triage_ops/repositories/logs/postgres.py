from triage_ops.db import SessionFactory
from triage_ops.tools.query_logs import Log

from .base import LogsRepository
from .schema import FindLogsArgs


class PostgresLogsRepository(LogsRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def find(self, args: FindLogsArgs) -> list[Log]:
        with self._session_factory() as _session:
            pass

        return []
