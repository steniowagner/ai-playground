from abc import ABC, abstractmethod

from .schema import (
    FeatureFlag,
    FindFeatureFlagsArgs,
)


class FeatureFlagsRepository(ABC):
    @abstractmethod
    def find(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        pass
