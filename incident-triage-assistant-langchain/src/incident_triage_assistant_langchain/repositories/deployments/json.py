import json
from pathlib import Path
from typing import Any

from incident_triage_assistant_langchain.tools.get_recent_deployments.schema import (
    Deployment,
)
from pydantic import ValidationError

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import DeploymentsRepository
from .schema import DeploymentsFixture, FindDeploymentsArgs

DEPLOYMENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "deployments.json"
)


class JSONDeploymentsRepository(DeploymentsRepository):
    def _parse_fixture(self, fixture_json: Any) -> DeploymentsFixture:
        try:
            return DeploymentsFixture.model_validate(fixture_json)
        except ValidationError as exc:
            raise RepositoryDataError("Deployments repository data is invalid") from exc

    def _read_deployments(self) -> list[Deployment]:
        try:
            with open(DEPLOYMENTS_FILE, "r", encoding="utf-8") as f:
                deployments_json = json.load(f)
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Deployments repository contains invalid text data."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RepositoryDataError(
                "Deployments repository contains invalid JSON."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable(
                "Deployments repository is unavailable."
            ) from exc

        fixture = self._parse_fixture(deployments_json)
        return fixture.deployments

    def find(self, args: FindDeploymentsArgs) -> list[Deployment]:
        all_deployments = self._read_deployments()

        deployments = [
            deployment
            for deployment in all_deployments
            if deployment.service == args.service
            and deployment.environment == args.environment
        ]

        matching_deployments = [
            deployment
            for deployment in deployments
            if deployment.started_at < args.completed_at
            and args.started_at < deployment.completed_at
        ]

        return sorted(
            matching_deployments,
            key=lambda deployment: deployment.completed_at,
            reverse=True,
        )
