---
title: Production Deployment Policy
department: Engineering
document_type: policy
effective_date: 2026-02-15
version: "3.1"
status: current
confidentiality: internal
---

# Production Deployment Policy

## Standard deployments

A production deployment requires a linked change record, successful required CI checks, an approved pull request, a rollback plan, and confirmation that monitoring is available. The engineer initiating the deployment must not be the sole code reviewer.

## Approvals

Low- and medium-risk deployments require approval from one qualified engineer other than the author. High-risk deployments require the service owner and an engineer from the platform or reliability team. Changes involving regulated data also require the Security or Privacy reviewer identified in the change record.

## Timing

High-risk deployments must occur during the service's published change window with an on-call responder available. Deployments during a company change freeze require incident commander approval for active incidents or VP Engineering approval for exceptional business needs.

## Emergency changes

An emergency change may proceed with approval from the incident commander and one qualified engineer. Normal documentation, review, and testing requirements must be completed retrospectively within one business day. Emergency status must not be used to accelerate routine feature work.

## Verification

The deployer must monitor relevant health indicators after release and record the result. If predefined rollback conditions occur, the deployer should roll back or invoke the incident process rather than continue experimenting in production.

