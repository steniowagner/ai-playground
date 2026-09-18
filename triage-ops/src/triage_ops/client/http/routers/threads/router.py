from fastapi import APIRouter
from triage_ops.client.http.utils import create_thread_id

from .schema import CreateThreadResponse

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("/")
def create_thread() -> CreateThreadResponse:
    return CreateThreadResponse(thread_id=create_thread_id())
