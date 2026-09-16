from ..schema import Service, ServiceResponse, ServiceSuccessResponse
from .schema import DisableFeatureFlagServiceArgs


class DisableFeatureFlagService(Service[DisableFeatureFlagServiceArgs]):
    def execute(self, args: DisableFeatureFlagServiceArgs) -> ServiceResponse:
        self.logger.warning(
            f"\n[Disable Feature-Flag Service]\nDisabling feature-flag. Args: {args.model_dump_json()}\n",
        )

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
