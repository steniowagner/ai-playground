from incident_triage_assistant.llm.factory import create_llm_client
from incident_triage_assistant.loop.agent_runner import AgentRunner
from incident_triage_assistant.tools.get_runbook.tool import get_runbook


def main() -> None:
    print(get_runbook({"runbook_id": "RB-CHECKOUT-ERRORS"}))
    return
    llm_client = create_llm_client("groq")
    agent_runner = AgentRunner(llm_client)
    agent_runner.run()
