import json
from pathlib import Path
from typing import Any

from incident_triage_assistant.tools.tool_response import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import Deployment, DeploymentsJson, GetRecentDeploymentsArgs

DEPLOYMENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "deployments.json"
)


def read_deployments() -> list[Deployment]:
    with open(DEPLOYMENTS_FILE, "r") as f:
        raw_deployments_json = json.load(f)
        deployments_json = DeploymentsJson.model_validate(raw_deployments_json)
        return deployments_json.deployments


def find_deployments(args: GetRecentDeploymentsArgs) -> list[Deployment]:
    all_deployments = read_deployments()

    deployments = [
        deployment
        for deployment in all_deployments
        if deployment.service == args.service
        and deployment.environment == args.environment
    ]

    if args.query_window:
        return [
            deployment
            for deployment in deployments
            if deployment.completed_at >= args.query_window.started_at
            and deployment.completed_at <= args.query_window.completed_at
        ]

    return deployments


def get_recent_deployments(raw_args: dict[str, Any]) -> ToolResponse:
    try:
        args = GetRecentDeploymentsArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
            ),
        )

    deployments = sorted(
        find_deployments(args), key=lambda x: x.completed_at, reverse=True
    )

    return ToolSuccessResponse(ok=True, data={"deployments": deployments})
