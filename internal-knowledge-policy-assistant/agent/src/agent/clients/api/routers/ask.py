from typing import Annotated

from agent.application.assistant import PolicyAssistant
from agent.clients.api.dependencies import get_policy_assistant
from agent.clients.api.schemas import AskRequest, AskResponse
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ask", tags=["ask"])

PolicyAssistantDependency = Annotated[PolicyAssistant, Depends(get_policy_assistant)]


@router.post("/")
def ask(request: AskRequest, assistant: PolicyAssistantDependency) -> AskResponse:
    answer = assistant.ask(
        question=request.question,
        top_k=request.top_k,
        min_score=request.min_score,
    )

    return AskResponse(
        content=answer.content,
        sources=answer.sources,
    )
