from ..exceptions import ServiceExecutionException
from ..schema import (
    Service,
    ServiceResponse,
    ServiceSuccessResponse,
)
from ..utils import wait_for_service_execution
from .schema import RestartServiceArgs


class RestartService(Service[RestartServiceArgs]):
    def execute(self, args: RestartServiceArgs) -> ServiceResponse:
        if not isinstance(args, RestartServiceArgs):
            raise TypeError("RestartService requires typed arguments.")

        try:
            self.logger.warning(
                f"\n[Restart Service]\nRestarting service. Args: {args.model_dump_json()}",
            )
        except Exception as exc:
            raise ServiceExecutionException("Failed to restart the service.") from exc

        wait_for_service_execution()

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
