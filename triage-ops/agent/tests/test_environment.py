import pytest
import triage_ops.graph.nodes.prepare_approvals.node as approvals_node
from triage_ops.graph.nodes.check_scope import RequestScope, ScopeDecision

from tests.support.factories import (
    make_advisory_proposal,
    make_ai_tool_message,
    make_approval_decision,
    make_deployment,
    make_disable_feature_flag_proposal,
    make_escalate_proposal,
    make_feature_flag,
    make_incident,
    make_investigation_response,
    make_investigation_result,
    make_log,
    make_maintenance_window,
    make_metric,
    make_pending_approval,
    make_restart_proposal,
    make_rollback_proposal,
    make_service_context,
    make_tool_call,
    make_tool_result,
)
from tests.support.fakes import (
    RecordingRepository,
    RecordingService,
    RecordingStreamWriter,
    ScriptedGraphModel,
    ScriptedModel,
)


@pytest.mark.unit
def test_shared_test_support_is_available() -> None:
    incident = make_incident()
    result = make_investigation_result()
    model = ScriptedModel([result])

    assert incident.incident_id == result.incident_id
    assert model.invoke([]) == result
    assert model.remaining_responses == 0


@pytest.mark.unit
def test_shared_factories_cover_common_test_contracts() -> None:
    call = make_tool_call("get_incident", {"incident_id": "INC-1042"})
    message = make_ai_tool_message(call)
    result = make_tool_result(call, ok=True)
    proposals = [
        make_rollback_proposal(),
        make_disable_feature_flag_proposal(),
        make_restart_proposal(),
        make_escalate_proposal(),
        make_advisory_proposal(),
    ]

    assert message.tool_calls[0]["name"] == call["name"]
    assert message.tool_calls[0]["args"] == call["args"]
    assert result.tool_call_id == call["id"]
    assert {proposal.kind for proposal in proposals} == {
        "rollback_deployment",
        "disable_feature_flag",
        "restart_service",
        "escalate_incident",
        "advisory",
    }
    assert make_pending_approval().proposal_id == make_approval_decision().proposal_id
    assert make_deployment().deployment_id == "dep-882"
    assert make_feature_flag().enabled is True
    assert make_log().severity == "ERROR"
    assert make_metric().values.error_rate == 8.4
    assert make_maintenance_window().maintenance_id == "MW-100"
    assert make_service_context().owner_team == "payments"


@pytest.mark.unit
def test_shared_fakes_record_calls_events_and_model_routes() -> None:
    repository = RecordingRepository(result={"found": True})
    service = RecordingService()
    writer = RecordingStreamWriter()
    response = make_investigation_response()
    model = ScriptedGraphModel(
        scopes=[ScopeDecision(scope=RequestScope.IN_SCOPE)],
        agent_messages=[make_ai_tool_message()],
        final_responses=[response],
    )

    assert repository.find("query") == {"found": True}
    assert repository.find_by_id("INC-1042") == {"found": True}
    assert repository.calls == ["query", "INC-1042"]
    assert service.execute({"action": "restart"}).ok is True
    writer({"event": "started"})
    assert writer.events == [{"event": "started"}]
    assert model.with_structured_output(ScopeDecision).invoke([]).scope == "in_scope"
    assert model.bind_tools([]).invoke([]).tool_calls == []
    assert model.with_structured_output(type(response)).invoke([]) == response


@pytest.mark.unit
async def test_async_tests_are_supported() -> None:
    async def operation() -> str:
        return "ready"

    assert await operation() == "ready"


@pytest.mark.unit
def test_deterministic_uuid_fixture(fixed_uuid: None) -> None:
    assert str(approvals_node.uuid4()) == "00000000-0000-0000-0000-000000000001"
