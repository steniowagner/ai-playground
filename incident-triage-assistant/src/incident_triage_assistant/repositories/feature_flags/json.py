import json
from pathlib import Path

from incident_triage_assistant.tools.get_feature_flags.schema import FeatureFlag

from .base import FeatureFlagsRepository
from .schema import FeatureFlagsFixture, FindFeatureFlagsArgs

FEATURE_FLAGS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "feature_flags.json"
)


class JSONFeatureFlagsRepository(FeatureFlagsRepository):
    def _read_feature_flags(self) -> list[FeatureFlag]:
        with open(FEATURE_FLAGS_FILE, "r", encoding="utf-8") as f:
            feature_flags_json = json.load(f)
            feature_flags_fixture = FeatureFlagsFixture.model_validate(
                feature_flags_json
            )
            return feature_flags_fixture.feature_flags

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
