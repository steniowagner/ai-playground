from incident_triage_assistant.tools.get_tool import get_tool


def main() -> None:
    tool = get_tool("get_incident")
    print(tool({"incident_id": "INC-1043"}))
