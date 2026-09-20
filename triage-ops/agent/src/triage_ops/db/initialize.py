from triage_ops.scripts.seed_db import seed_db
from triage_ops.utils import get_settings

from .utils import (
    create_database_engine,
    create_database_schema,
    create_session_factory,
)


def initialize_database() -> None:
    settings = get_settings()
    db_engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(db_engine)

    try:
        create_database_schema(db_engine)
        seed_db(session_factory)
    finally:
        db_engine.dispose()


if __name__ == "__main__":
    initialize_database()
