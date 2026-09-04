import json
from pathlib import Path
from typing import Any

from incident_triage_assistant_langchain.tools.get_feature_flags.schema import (
    FeatureFlag,
)
from pydantic import ValidationError

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import FeatureFlagsRepository
from .schema import FeatureFlagsFixture, FindFeatureFlagsArgs

FEATURE_FLAGS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "feature_flags.json"
)


class JSONFeatureFlagsRepository(FeatureFlagsRepository):
    def _parse_fixture(self, fixture_json: Any) -> FeatureFlagsFixture:
        try:
            return FeatureFlagsFixture.model_validate(fixture_json)
        except ValidationError as exc:
            raise RepositoryDataError(
                "Feature-flags repository data is invalid."
            ) from exc

    def _read_feature_flags(self) -> list[FeatureFlag]:
        try:
            with open(FEATURE_FLAGS_FILE, "r", encoding="utf-8") as f:
                feature_flags_json = json.load(f)
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Feature-flags repository contains invalid text data."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RepositoryDataError(
                "Feature-flags repository contains invalid JSON."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable(
                "Feature-flags repository is unavailable."
            ) from exc

        fixture = self._parse_fixture(feature_flags_json)
        return fixture.feature_flags

    def _find_feature_flags(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        all_feature_flags = self._read_feature_flags()

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

    def find(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        return sorted(
            self._find_feature_flags(args), key=lambda feature_flag: feature_flag.flag
        )
