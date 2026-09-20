from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from triage_ops.db import create_database_engine, create_session_factory
from triage_ops.repositories.sample_questions import JSONSampleQuestionsRepository
from triage_ops.utils import get_settings

from .routers.sample_questions import sample_questions
from .routers.threads import threads_router
from .utils import create_graph_runner

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    database_engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(database_engine)

    app.state.graph_runner = create_graph_runner(session_factory)
    app.state.sample_questions_repository = JSONSampleQuestionsRepository()

    try:
        yield
    finally:
        del app.state.graph_runner
        del app.state.sample_questions_repository
        database_engine.dispose()


app = FastAPI(
    title="Incident Triage Assistant Engine", version="1.0", lifespan=lifespan
)

app.include_router(threads_router)
app.include_router(sample_questions)
