from agent.application.assistant import PolicyAssistant
from fastapi import Request


def get_policy_assistant(request: Request) -> PolicyAssistant:
    return request.app.state.policy_assistant
