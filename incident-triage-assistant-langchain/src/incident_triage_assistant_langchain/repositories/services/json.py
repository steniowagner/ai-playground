import json
from pathlib import Path
from typing import Any

from incident_triage_assistant_langchain.tools.get_service_context.schema import Service
from pydantic import ValidationError

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import ServicesRepository
from .schema import FindServiceArgs, ServicesFixture

SERVICES_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "services.json"
)


class JSONServicesRepository(ServicesRepository):
    def _parse_fixture(self, fixture_json: Any) -> ServicesFixture:
        try:
            return ServicesFixture.model_validate(fixture_json)
        except ValidationError as exc:
            raise RepositoryDataError("Services repository data is invalid.") from exc

    def _read_services(self) -> list[Service]:
        try:
            with open(SERVICES_FILE, "r", encoding="utf-8") as f:
                services_json = json.load(f)
        except json.JSONDecodeError as exc:
            raise RepositoryDataError(
                "Services repository contains invalid JSON."
            ) from exc
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Services repository contains invalid text data."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable("Services repository is unavailable.") from exc

        fixture = self._parse_fixture(services_json)
        return fixture.services

    def find(self, args: FindServiceArgs) -> Service | None:
        services = self._read_services()

        return next(
            iter(
                filter(
                    lambda item: (
                        item.service == args.service
                        and args.environment in item.environments
                    ),
                    services,
                )
            ),
            None,
        )
