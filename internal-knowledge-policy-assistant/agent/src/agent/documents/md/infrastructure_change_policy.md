---
title: Infrastructure Change Policy
department: Engineering
document_type: policy
effective_date: 2026-02-15
version: "2.8"
status: current
confidentiality: internal
---

# Infrastructure Change Policy

## Infrastructure as code

Production infrastructure must be managed through approved infrastructure-as-code repositories wherever the platform supports it. Manual console changes are prohibited except during an incident or when no supported automation exists.

## Change record

Every material infrastructure change requires an owner, purpose, affected systems, risk classification, test evidence, implementation plan, rollback plan, and monitoring plan. High-risk changes require review by the platform team and affected service owners.

## Database changes

Schema migrations must be backward compatible during phased deployment unless an approved maintenance window is used. Destructive migrations require a verified backup, restoration plan, data-owner approval, and explicit confirmation that retention obligations are satisfied.

## Emergency changes and reconciliation

Manual emergency changes require an active incident record and incident commander approval. The responder must record commands or actions taken. The system must be reconciled back into infrastructure as code within one business day after the incident is stabilized.

## Drift

Detected configuration drift must be investigated. Teams must not automatically overwrite unexplained drift when doing so could increase customer impact or destroy evidence of a security event.

