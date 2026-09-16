from ..exceptions import ServiceExecutionException
from ..schema import Service, ServiceResponse, ServiceSuccessResponse
from .schema import RollbackDeploymentServiceArgs


class RoolbackDeploymentService(Service[RollbackDeploymentServiceArgs]):
    def execute(self, args: RollbackDeploymentServiceArgs) -> ServiceResponse:
        if not isinstance(args, RollbackDeploymentServiceArgs):
            raise TypeError("RoolbackDeploymentService requires typed arguments.")

        try:
            self.logger.warning(
                f"\n[Rollback Deployment Service]\nReverting deployment. Args: {args.model_dump_json()}",
            )
        except Exception as exc:
            raise ServiceExecutionException(
                "Failed to roll back the deployment."
            ) from exc

        return ServiceSuccessResponse(ok=True, data=args.model_dump(mode="json"))
