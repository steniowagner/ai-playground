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

from .schema import (
    FeatureFlag,
    FeatureFlagsFixture,
    GetFeatureFlagsArgs,
    GetFeatureFlagsResult,
)

FEATURE_FLAGS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "feature_flags.json"
)


def read_feature_flags() -> list[FeatureFlag]:
    with open(FEATURE_FLAGS_FILE, "r", encoding="utf-8") as f:
        feature_flags_json = json.load(f)
        feature_flags_fixture = FeatureFlagsFixture.model_validate(feature_flags_json)
        return feature_flags_fixture.feature_flags


def find_feature_flags(args: GetFeatureFlagsArgs) -> list[FeatureFlag]:
    all_feature_flags = read_feature_flags()

    def filter_feature_flag(feature_flag: FeatureFlag) -> bool:
        if args.flag_name is not None:
            return (
                feature_flag.service == args.service
                and feature_flag.environment == args.environment
                and feature_flag.flag == args.flag_name
            )

        return (
            feature_flag.service == args.service
            and feature_flag.environment == args.environment
        )

    return [
        feature_flag
        for feature_flag in all_feature_flags
        if filter_feature_flag(feature_flag)
    ]


def get_feature_flags(raw_args: dict[str, Any]) -> ToolResponse[GetFeatureFlagsResult]:
    try:
        args = GetFeatureFlagsArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'."
            ),
        )

    feature_flags = sorted(
        find_feature_flags(args), key=lambda feature_flag: feature_flag.flag
    )

    return ToolSuccessResponse(
        ok=True, data=GetFeatureFlagsResult(feature_flags=feature_flags)
    )
