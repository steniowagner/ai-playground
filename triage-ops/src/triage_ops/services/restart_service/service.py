from ..schema import Service, ServiceResponse, ServiceSuccessResponse
from .schema import RestartServiceArgs


class RestartService(Service[RestartServiceArgs]):
    def execute(self, args: RestartServiceArgs) -> ServiceResponse:
        self.logger.warning(
            f"\n[Restart Service]\nRestarting service. Args: {args.model_dump_json()}",
        )

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
