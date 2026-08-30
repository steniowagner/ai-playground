import json
from pathlib import Path
from typing import Any

from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetServiceContextArgs,
    GetServiceContextResult,
    Service,
    ServicesFixture,
)

SERVICES_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "services.json"
)


def read_services() -> list[Service]:
    with open(SERVICES_FILE, "r", encoding="utf-8") as f:
        raw_services_json = json.load(f)
        services_json = ServicesFixture.model_validate(raw_services_json)
        return services_json.services


def find_service(args: GetServiceContextArgs) -> Service | None:
    services = read_services()

    return next(
        iter(
            filter(
                lambda x: (
                    x.service == args.service and args.environment in x.environments
                ),
                services,
            )
        ),
        None,
    )


def get_service_context(raw_args: dict[str, Any]) -> ToolResponse:
    try:
        args = GetServiceContextArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
            ),
        )

    service = find_service(args)

    if not service:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="NOT_FOUND",
                message=f"Service '{args.service}' running in '{args.environment}' not found.",
            ),
        )

    return ToolSuccessResponse(ok=True, data=GetServiceContextResult(service=service))
