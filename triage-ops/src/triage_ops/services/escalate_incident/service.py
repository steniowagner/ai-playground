from ..exceptions import ServiceExecutionException
from ..schema import Service, ServiceResponse, ServiceSuccessResponse
from .schema import EscalateIncidentServiceArgs


class EscalateIncidentService(Service[EscalateIncidentServiceArgs]):
    def execute(self, args: EscalateIncidentServiceArgs) -> ServiceResponse:
        if not isinstance(args, EscalateIncidentServiceArgs):
            raise TypeError("EscalateIncidentService requires typed arguments.")

        try:
            self.logger.warning(
                f"\n[Escalate Incident Service]\nEscalating incident. Args: {args.model_dump_json()}\n",
            )
        except Exception as exc:
            raise ServiceExecutionException("Failed to escalate the incident.") from exc

        return ServiceSuccessResponse(
            ok=True,
            data=args.model_dump(mode="json"),
        )
