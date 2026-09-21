import asyncio

from triage_ops.client.cli.run_cli import run_cli
from triage_ops.db import create_database_engine, create_session_factory
from triage_ops.utils import get_settings

from .create_graph_runner import create_graph_runner


def app() -> None:
    settings = get_settings()
    database_engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(database_engine)

    graph_runner = create_graph_runner(session_factory)

    asyncio.run(
        run_cli(
            graph_runner=graph_runner,
            thread_id="cli",
        )
    )


__all__ = ["app"]
