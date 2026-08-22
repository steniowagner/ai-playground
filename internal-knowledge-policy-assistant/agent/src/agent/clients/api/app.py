from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from agent.application.bootstrap import create_policy_assistant
from agent.clients.api.routers.ask import router as ask_router
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.policy_assistant = create_policy_assistant()
    yield
    del app.state.policy_assistant


app = FastAPI(
    title="Internal Knowledge Policy Assitant API", version="1.0", lifespan=lifespan
)

app.include_router(ask_router)
