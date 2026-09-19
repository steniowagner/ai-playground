from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from triage_ops.repositories.sample_questions import JSONSampleQuestionsRepository

from .routers.sample_questions import sample_questions
from .routers.threads import threads_router
from .utils import create_graph_runner

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.graph_runner = create_graph_runner()
    app.state.sample_questions_repository = JSONSampleQuestionsRepository()

    yield

    del app.state.graph_runner
    del app.state.sample_questions_repository


app = FastAPI(
    title="Incident Triage Assistant Engine", version="1.0", lifespan=lifespan
)

app.include_router(threads_router)
app.include_router(sample_questions)
