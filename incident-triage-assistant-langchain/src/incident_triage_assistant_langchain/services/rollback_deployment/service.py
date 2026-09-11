from ..schema import ServiceResponse, ServiceSuccessResponse
from ..service import Service
from .schema import RollbackDeploymentServiceArgs


class RoolbackDeploymentService(Service[RollbackDeploymentServiceArgs]):
    def execute(self, args: RollbackDeploymentServiceArgs) -> ServiceResponse:
        self.logger.warning(
            f"Reverting deployment. Args: {args.model_dump_json()}",
        )

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
