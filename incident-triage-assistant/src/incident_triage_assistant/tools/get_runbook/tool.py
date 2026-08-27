from pathlib import Path
from typing import Any

from incident_triage_assistant.tools.tool_response import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import GetRunbookArgs, GetRunbookResult

RUNBOOKS_DIR = Path(__file__).resolve().parents[4] / "data" / "runbooks"


def read_runbooks() -> list[str]:
    runbook_dir = Path(RUNBOOKS_DIR)

    return [f.stem for f in runbook_dir.iterdir() if f.is_file() and f.suffix == ".md"]


def read_runbook(runbook_id: str) -> str:
    runbook_path = Path(RUNBOOKS_DIR / f"{runbook_id}.md")

    return runbook_path.read_text(encoding="utf-8")


def get_runbook(raw_args: dict[str, Any]) -> ToolResponse[GetRunbookResult]:
    try:
        args = GetRunbookArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'."
            ),
        )

    runbooks = read_runbooks()

    if args.runbook_id not in runbooks:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="NOT_FOUND",
                message=f"Runbook '{args.runbook_id}' not found.",
            ),
        )

    runbook_content = read_runbook(args.runbook_id)

    return ToolSuccessResponse(
        ok=True,
        data=GetRunbookResult(runbook_id=args.runbook_id, content=runbook_content),
    )
