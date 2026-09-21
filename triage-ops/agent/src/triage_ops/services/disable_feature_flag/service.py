from ..exceptions import ServiceExecutionException
from ..schema import (
    Service,
    ServiceResponse,
    ServiceSuccessResponse,
)
from ..utils import wait_for_service_execution
from .schema import DisableFeatureFlagServiceArgs


class DisableFeatureFlagService(Service[DisableFeatureFlagServiceArgs]):
    def execute(self, args: DisableFeatureFlagServiceArgs) -> ServiceResponse:
        if not isinstance(args, DisableFeatureFlagServiceArgs):
            raise TypeError("DisableFeatureFlagService requires typed arguments.")

        try:
            self.logger.warning(
                f"\n[Disable Feature-Flag Service]\nDisabling feature-flag. Args: {args.model_dump_json()}\n",
            )
        except Exception as exc:
            raise ServiceExecutionException(
                "Failed to disable the feature flag."
            ) from exc

        wait_for_service_execution()

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
