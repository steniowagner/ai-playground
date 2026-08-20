---
title: Engineering Handbook
department: Engineering
document_type: handbook
effective_date: 2026-01-15
version: "6.0"
status: current
confidentiality: internal
---

# Engineering Handbook

## Ownership

Every production service must have an owning team, an on-call rotation, a service catalog entry, operational dashboards, and a current runbook. The owning team is accountable for reliability and lifecycle decisions.

## Development workflow

Changes are developed on short-lived branches and submitted through pull requests. Direct commits to protected branches are prohibited. Code review requirements are defined in the Code Review Guidelines; production release requirements are defined in the Deployment Policy.

## Testing

Teams must maintain automated tests proportional to the risk of the service. Changes to authorization, payments, data deletion, or encryption require tests for both expected and denied behavior. A passing test suite does not replace reviewer judgment.

## Documentation

Material architecture decisions must be recorded in an architecture decision record. Public interfaces and operational procedures must be documented before launch. Runbooks must state how to diagnose, mitigate, escalate, and recover from common failures.

## Production access

Engineers do not receive production access automatically. Access is governed by the Production Access Policy and should be used only for approved operational purposes.

