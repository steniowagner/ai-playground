---
title: Incident Response Guide
department: Engineering
document_type: runbook
effective_date: 2026-03-01
version: "5.3"
status: current
confidentiality: internal
---

# Incident Response Guide

## Declaring an incident

Declare an incident when a production event causes or threatens significant customer impact, data loss, security exposure, or sustained failure of a critical service. When uncertain, declare early; incidents may be downgraded later.

## Severity

SEV-1 is a widespread outage, confirmed sensitive-data compromise, or event threatening company continuity. SEV-2 is substantial degradation or limited customer impact without a viable routine workaround. SEV-3 is a contained issue requiring coordinated attention but not an emergency response.

## Initial response

The first responder opens an incident channel, creates an incident record, assigns an incident commander, and begins a timeline. The incident commander coordinates decisions and delegates technical investigation. A communications lead handles stakeholder updates so responders can focus on mitigation.

## Escalation and communication

SEV-1 incidents page the executive duty officer, Security, Legal, and Communications immediately. SEV-2 incidents page the owning team's manager and central reliability team. Internal updates are due every 30 minutes for SEV-1 and every 60 minutes for SEV-2. Only authorized Communications or Legal personnel may communicate externally.

## Recovery and review

Recovery must be verified using customer-facing indicators, not solely internal component health. A blameless post-incident review is required within five business days for SEV-1 and SEV-2 incidents. Corrective actions must have owners and due dates.

