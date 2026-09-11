from ..schema import ServiceResponse, ServiceSuccessResponse
from ..service import Service
from .schema import DisableFeatureFlagServiceArgs


class DisableFeatureFlagService(Service[DisableFeatureFlagServiceArgs]):
    def execute(self, args: DisableFeatureFlagServiceArgs) -> ServiceResponse:
        self.logger.info(
            f"Disabling feature-flag. Args: {args.model_dump_json()}",
        )

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
