from ..schema import ServiceResponse, ServiceSuccessResponse
from ..service import Service
from .schema import RestartServiceArgs


class RestartServiceTool(Service[RestartServiceArgs]):
    def execute(self, args: RestartServiceArgs) -> ServiceResponse:
        self.logger.info(
            f"Restarting service. Args: {args.model_dump_json()}",
        )

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
