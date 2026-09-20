from triage_ops.db.schema import SessionFactory

from .seed_logs import seed_logs


def seed_db(session_factory: SessionFactory) -> None:
    seed_logs()


if __name__ == "__main__":
    seed_db()
