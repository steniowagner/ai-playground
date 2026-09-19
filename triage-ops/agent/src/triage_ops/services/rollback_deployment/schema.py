from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from triage_ops.domain import (
    Environment,
)


class RollbackDeploymentServiceArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str = Field(
        min_length=1,
        description=(
            "Service whose deployment should be reverted, copied exactly from a "
            "successful tool result. This is not always the incident's own "
            "service; a dependency may be the deployment that must be reverted."
        ),
    )

    environment: Environment = Field(
        description=(
            "Environment the deployment is live in, copied exactly from the "
            "deployment record. Never assume production."
        )
    )

    deployment_id: str = Field(
        min_length=1,
        description=(
            "Identifier of the deployment to revert, copied exactly from "
            "get_recent_deployments. Never construct or guess this value."
        ),
    )

    target_deployment_id: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Identifier of the known-good deployment to restore, copied exactly "
            "from get_recent_deployments. Null means restore the deployment that "
            "immediately preceded deployment_id. Provide a value only when "
            "evidence shows the immediately preceding deployment is also suspect."
        ),
    )
