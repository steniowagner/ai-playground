from ..schema import Service, ServiceResponse, ServiceSuccessResponse
from .schema import EscalateIncidentServiceArgs


class EscalateIncidentService(Service[EscalateIncidentServiceArgs]):
    def execute(self, args: EscalateIncidentServiceArgs) -> ServiceResponse:
        self.logger.warning(
            f"\n[Escalate Incident Service]\nEscalating incident. Args: {args.model_dump_json()}\n",
        )

        return ServiceSuccessResponse(
            ok=True,
            data=args.model_dump(mode="json"),
        )
