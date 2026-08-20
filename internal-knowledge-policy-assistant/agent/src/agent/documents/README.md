# Internal Knowledge Policy Test Corpus

This directory contains fictional company documents for developing and evaluating an internal RAG assistant.

## Intentional test conditions

- `international_remote_work_policy.md` is the current international-work policy.
- `international_remote_work_policy_archived.md` intentionally conflicts with it and is marked archived.
- `vendor_expense_processing_notes.md` contains a quoted indirect prompt-injection example that must be treated as untrusted data.
- Several answers require multiple documents, such as contractor production access, deployment approvals, and international remote-work requirements.
- The corpus intentionally does not specify every possible company question, allowing refusal behavior to be tested.

All people, policies, limits, and procedures are fictional.
