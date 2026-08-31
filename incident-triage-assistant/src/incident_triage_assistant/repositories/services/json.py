import json
from pathlib import Path

from incident_triage_assistant.domain.types import Environment
from incident_triage_assistant.tools.get_service_context.schema import Service

from .base import ServicesRepository
from .schema import (
    ServicesFixture,
)

SERVICES_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "services.json"
)


class JSONServicesRepository(ServicesRepository):
    def _read_services(self) -> list[Service]:
        with open(SERVICES_FILE, "r", encoding="utf-8") as f:
            raw_services_json = json.load(f)
            services_json = ServicesFixture.model_validate(raw_services_json)
            return services_json.services

    def find(self, service: str, environment: Environment) -> Service | None:
        services = self._read_services()

        return next(
            iter(
                filter(
                    lambda x: x.service == service and environment in x.environments,
                    services,
                )
            ),
            None,
        )
