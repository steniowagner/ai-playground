---
title: Information Security Policy
department: Information Security
document_type: policy
effective_date: 2026-01-01
version: "7.0"
status: current
confidentiality: internal
---

# Information Security Policy

## Account security

Employees must use unique company identities, approved password management, and phishing-resistant MFA where supported. Credentials, API keys, and session tokens must not be shared through chat, email, source code, or tickets.

## Devices and software

Company information may be accessed only from managed devices unless Security has approved an exception. Security updates must not be disabled. Unapproved browser extensions and software that transmit company data are prohibited.

## Vulnerability reporting

An engineer who discovers a suspected vulnerability must stop unnecessary testing, preserve relevant evidence, and report it immediately through the Security Incident channel. The report should include the affected system, observed behavior, potential impact, and safe reproduction steps. The engineer must not exploit the issue further, access unrelated data, contact affected customers, or disclose it publicly without Security authorization.

## Secrets exposure

Exposed credentials must be treated as compromised even if quickly deleted. Notify Security, revoke or rotate the credential, review usage logs, and remove the secret from repository history using the approved procedure.

## Exceptions

Policy exceptions require a documented risk assessment, compensating controls, an owner, an expiration date, and approval from Information Security. Manager approval alone is insufficient.

