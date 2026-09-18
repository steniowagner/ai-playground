from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.graph import (
    GraphRunner,
    build_graph,
)
from triage_ops.model import create_model

from .routers.graph import router as graph_routes

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    model = create_model("anthropic")
    checkpointer = InMemorySaver()
    graph = build_graph(model, checkpointer)
    app.state.graph_runner = GraphRunner(graph)
    yield
    del app.state.graph_runner


app = FastAPI(
    title="Incident Triage Assistant Engine", version="1.0", lifespan=lifespan
)

app.include_router(graph_routes)
