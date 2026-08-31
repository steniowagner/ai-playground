from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.feature_flags.base import (
    FeatureFlagsRepository,
)
from incident_triage_assistant.tools.get_feature_flags.schema import FeatureFlag
from incident_triage_assistant.tools.get_feature_flags.tool import GetFeatureFlagsTool
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def feature_flag() -> FeatureFlag:
    return FeatureFlag.model_validate(
        {
            "flag": "new_checkout",
            "service": "checkout-api",
            "environment": "production",
            "enabled": True,
            "owner_team": "payments",
            "changed_at": "2026-08-20T10:00:00Z",
            "changed_by_deployment": "dep-1",
        }
    )


def test_returns_repository_results_and_forwards_filters() -> None:
    repository = Mock(spec=FeatureFlagsRepository)
    repository.find.return_value = [feature_flag()]

    response = GetFeatureFlagsTool(repository)(
        {
            "service": "checkout-api",
            "environment": "production",
            "flag_name": "new_checkout",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.data.feature_flags == [feature_flag()]
    args = repository.find.call_args.args[0]
    assert (args.service, args.environment, args.flag_name) == (
        "checkout-api",
        "production",
        "new_checkout",
    )


def test_returns_empty_success_for_no_matches() -> None:
    repository = Mock(spec=FeatureFlagsRepository)
    repository.find.return_value = []
    response = GetFeatureFlagsTool(repository)(
        {"service": "checkout-api", "environment": "production"}
    )
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.feature_flags == []


@pytest.mark.parametrize(
    "args",
    [
        {},
        {"service": "checkout-api", "environment": "unknown"},
        {"service": "checkout-api", "environment": "production", "flag_name": ""},
    ],
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=FeatureFlagsRepository)
    response = GetFeatureFlagsTool(repository)(args)
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find.assert_not_called()
