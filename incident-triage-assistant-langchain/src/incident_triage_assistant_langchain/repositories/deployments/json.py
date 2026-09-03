import json
from pathlib import Path

from incident_triage_assistant_langchain.tools.get_recent_deployments.schema import (
    Deployment,
)

from .base import DeploymentsRepository
from .schema import DeploymentsFixture, FindDeploymentsArgs

DEPLOYMENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "deployments.json"
)


class JSONDeploymentsRepository(DeploymentsRepository):
    def _read_deployments(self) -> list[Deployment]:
        with open(DEPLOYMENTS_FILE, "r") as f:
            raw_deployments_json = json.load(f)
            deployments_json = DeploymentsFixture.model_validate(raw_deployments_json)
            return deployments_json.deployments

    def find(self, args: FindDeploymentsArgs) -> list[Deployment]:
        all_deployments = self._read_deployments()

        deployments = [
            deployment
            for deployment in all_deployments
            if deployment.service == args.service
            and deployment.environment == args.environment
        ]

        if args.started_at and args.completed_at:
            matching_deployments = [
                deployment
                for deployment in deployments
                if deployment.completed_at >= args.started_at
                and deployment.completed_at <= args.completed_at
            ]

            return sorted(
                matching_deployments,
                key=lambda deployment: deployment.completed_at,
                reverse=True,
            )

        return sorted(
            deployments,
            key=lambda deployment: deployment.completed_at,
            reverse=True,
        )
