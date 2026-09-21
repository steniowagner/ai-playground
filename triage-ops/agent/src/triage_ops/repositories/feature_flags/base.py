from abc import ABC, abstractmethod

from triage_ops.domain import FeatureFlag

from .schema import (
    FindFeatureFlagsArgs,
)


class FeatureFlagsRepository(ABC):
    @abstractmethod
    def find(self, args: FindFeatureFlagsArgs) -> list[FeatureFlag]:
        pass

    @abstractmethod
    def find_all(self) -> list[FeatureFlag]:
        pass
