import logging
from abc import ABC, abstractmethod

from .schema import ServiceResponse


class Service[Args](ABC):
    def __init__(self):
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def execute(self, args: Args) -> ServiceResponse:
        pass
