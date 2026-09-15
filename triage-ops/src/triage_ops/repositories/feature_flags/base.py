from abc import ABC, abstractmethod

from triage_ops.tools.get_feature_flags.schema import (
    FeatureFlag,
)

from .schema import FindFeatureFlagsArgs


class FeatureFlagsRepository(ABC):
    @abstractmethod
    def find(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        pass
