from ..schema import ServiceResponse, ServiceSuccessResponse
from ..service import Service
from .schema import EscalateIncidentServiceArgs


class EscalateIncidentService(Service[EscalateIncidentServiceArgs]):
    def execute(self, args: EscalateIncidentServiceArgs) -> ServiceResponse:
        self.logger.info(
            f"Escalating incident. Args: {args.model_dump_json()}",
        )

        return ServiceSuccessResponse(
            ok=True,
            data=args.model_dump(mode="json"),
        )
