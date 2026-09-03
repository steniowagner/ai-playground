from abc import ABC, abstractmethod

from incident_triage_assistant_langchain.tools.get_feature_flags.schema import (
    FeatureFlag,
)

from .schema import FindFeatureFlagsArgs


class FeatureFlagsRepository(ABC):
    @abstractmethod
    def find(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        pass
