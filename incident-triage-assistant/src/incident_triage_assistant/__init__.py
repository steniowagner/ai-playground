from incident_triage_assistant.llm.factory import create_llm_client
from incident_triage_assistant.loop.agent_runner import AgentRunner


def main() -> None:
    llm_client = create_llm_client("groq")
    agent_runner = AgentRunner(llm_client)
    agent_runner.run()
