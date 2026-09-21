import logging

from triage_ops.db.schema import SessionFactory

from .exceptions import SeedDatabaseException
from .seed_deployments import seed_deployments
from .seed_feature_flags import seed_feature_flags
from .seed_incidents import seed_incidents
from .seed_logs import seed_logs
from .seed_maintenance_windows import seed_maintenance_windows


def seed_db(session_factory: SessionFactory) -> None:
    logger = logging.getLogger(__name__)
    logger.warning("[Seeding Database]")

    try:
        seed_logs(session_factory, logger)
        seed_incidents(session_factory, logger)
        seed_feature_flags(session_factory, logger)
        seed_maintenance_windows(session_factory, logger)
        seed_deployments(session_factory, logger)
    except SeedDatabaseException:
        logger.exception("Database seeding failed.")
        raise


if __name__ == "__main__":
    seed_db()
