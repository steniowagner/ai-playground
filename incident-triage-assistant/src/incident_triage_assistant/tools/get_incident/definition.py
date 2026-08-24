from .schema import GetIncidentParams

GET_INCIDENT_TOOL = {
    "name": "get_incident",
    "description": "Get an incident by its exact ID.",
    "parameters": GetIncidentParams.model_json_schema(),
}
