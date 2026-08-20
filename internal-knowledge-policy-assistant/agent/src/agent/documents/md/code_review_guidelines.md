---
title: Code Review Guidelines
department: Engineering
document_type: standard
effective_date: 2026-01-20
version: "3.0"
status: current
confidentiality: internal
---

# Code Review Guidelines

## Required review

Every change to production code, infrastructure definitions, deployment configuration, or security controls requires review through the approved source-control system. Authors may not approve their own changes.

## Number and type of reviewers

Ordinary changes require one qualified reviewer. Changes to authentication, authorization, cryptography, payment handling, personal-data processing, or destructive database operations require two reviewers, including the relevant Security, Privacy, or data owner specified by repository rules.

## Reviewer responsibilities

Reviewers evaluate correctness, security, failure behavior, tests, observability, maintainability, and compatibility. Approval means the reviewer believes the change is safe to merge; it is not merely confirmation that formatting checks passed.

## Author responsibilities

Pull requests should be small enough to review, explain why the change is needed, describe testing, identify risk, and link applicable tickets. Authors must resolve or explicitly respond to comments. Material changes after approval require renewed review.

## Exceptions

Emergency review rules are defined by the Deployment Policy. Pair programming does not replace recorded approval for production changes.

