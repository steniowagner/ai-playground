from incident_triage_assistant.tools.get_tools import (
    get_tools,
)


def test_get_tools() -> None:
    tools = get_tools()

    for tool in tools:
        assert isinstance(tool.name, str)
        assert isinstance(tool.description, str)
        assert isinstance(tool.args, object)
