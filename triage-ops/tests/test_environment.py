import pytest
import triage_ops.graph.nodes.prepare_approvals.node as approvals_node

from tests.support.factories import make_incident, make_investigation_result
from tests.support.fakes import ScriptedModel


@pytest.mark.unit
def test_shared_test_support_is_available() -> None:
    incident = make_incident()
    result = make_investigation_result()
    model = ScriptedModel([result])

    assert incident.incident_id == result.incident_id
    assert model.invoke([]) == result
    assert model.remaining_responses == 0


@pytest.mark.unit
async def test_async_tests_are_supported() -> None:
    async def operation() -> str:
        return "ready"

    assert await operation() == "ready"


@pytest.mark.unit
def test_deterministic_uuid_fixture(fixed_uuid: None) -> None:
    assert str(approvals_node.uuid4()) == "00000000-0000-0000-0000-000000000001"
