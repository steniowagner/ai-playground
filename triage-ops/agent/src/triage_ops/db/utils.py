from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from .models.base import Base
from .schema import SessionFactory


def create_database_engine(url: str) -> Engine:
    return create_engine(url)


def create_database_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def create_session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
