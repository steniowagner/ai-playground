from incident_triage_assistant_langchain.nodes.schema import Nodes

from .schema import StreamUpdate


def handle_update_event(payload: dict) -> StreamUpdate:
    if "__interrupt__" in payload:
        interruptions = payload["__interrupt__"]

        return (
            StreamUpdate(approval_request=interruptions[0].value)
            if interruptions
            else StreamUpdate()
        )

    finalizer_update = payload.get(Nodes.FINALIZER)

    if finalizer_update is not None:
        return StreamUpdate(final_result=finalizer_update.get("final_result"))

    return StreamUpdate()
