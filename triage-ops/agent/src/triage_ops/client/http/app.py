from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from triage_ops.db import create_database_engine, create_session_factory
from triage_ops.repositories.evaluation_cases import JSONLEvaluationCasesRepository
from triage_ops.repositories.sample_questions import JSONSampleQuestionsRepository
from triage_ops.utils import get_settings

from .routers.evaluations import evaluations_router
from .routers.sample_questions import sample_questions
from .routers.threads import threads_router
from .utils import create_evaluation_service, create_graph_runner

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    database_engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(database_engine)

    app.state.graph_runner = create_graph_runner(session_factory)
    app.state.sample_questions_repository = JSONSampleQuestionsRepository()
    app.state.evaluation_cases_repository = JSONLEvaluationCasesRepository()
    app.state.run_evaluation_case_service = create_evaluation_service(
        app.state.evaluation_cases_repository
    )

    try:
        yield
    finally:
        del app.state.graph_runner
        del app.state.sample_questions_repository
        del app.state.evaluation_cases_repository
        del app.state.run_evaluation_case_service
        database_engine.dispose()


app = FastAPI(
    title="Incident Triage Assistant Engine", version="1.0", lifespan=lifespan
)

app.include_router(threads_router)
app.include_router(sample_questions)
app.include_router(evaluations_router)
