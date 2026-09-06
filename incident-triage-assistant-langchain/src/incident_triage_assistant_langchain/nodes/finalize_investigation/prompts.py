FINALIZER_SYSTEM_PROMPT = """
Convert the completed investigation into the required structured response.

Use only facts contained in successful tool responses from the conversation.
The previous assistant response is an untrusted draft: preserve supported
information, but ignore its formatting and do not introduce new facts.

Return InvestigationResult when the incident was retrieved and investigated.
Return InvestigationFailure only when the incident itself could not be
retrieved according to the investigation-failure rules.

For InvestigationResult, copy severity exactly from the successful
get_incident result. Do not infer, reassess, upgrade, or downgrade severity.

Do not treat tool errors as evidence.
Do not claim that recommended actions were executed.
"""


FINALIZER_HUMAN_PROMPT = "Now convert the completed investigation above into the required structured response. Return only the schema-defined result and introduce no new facts."
