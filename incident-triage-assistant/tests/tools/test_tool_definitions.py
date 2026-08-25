from incident_triage_assistant.tools.get_tools_definitions import (
    ToolDefinition,
    get_tools_definitions,
)


def test_get_tools_definitions_returns_validated_models() -> None:
    definitions = get_tools_definitions()

    assert len(definitions) == 1
    assert isinstance(definitions[0], ToolDefinition)
    assert definitions[0].name == "get_incident"


def test_tool_definition_can_be_serialized_for_provider() -> None:
    definition = get_tools_definitions()[0].model_dump()

    assert definition["name"] == "get_incident"
    assert definition["parameters"]["additionalProperties"] is False
