import logging

from triage_ops.db.schema import SessionFactory

from .exceptions import SeedDatabaseException
from .seed_incidents import seed_incidents
from .seed_logs import seed_logs


def seed_db(session_factory: SessionFactory) -> None:
    logger = logging.getLogger(__name__)
    logger.warning("[Seeding Database]")

    try:
        seed_logs(session_factory, logger)
        seed_incidents(session_factory, logger)
    except SeedDatabaseException:
        logger.exception("Database seeding failed.")
        raise


if __name__ == "__main__":
    seed_db()
