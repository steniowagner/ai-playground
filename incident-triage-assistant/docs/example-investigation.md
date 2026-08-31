# Reference investigation: INC-1042

This is a representative successful transcript built from the repository’s fictional fixtures. It documents the intended end-to-end behavior; it is not presented as a verbatim capture from a live Groq request.

## Operator request

```text
investigate the incident INC-1042
```

## Agent tool sequence

```text
1. get_incident
   incident_id: INC-1042

2. get_service_context
   service: checkout-api
   environment: production

3. get_recent_deployments
   service: checkout-api
   environment: production
   incident-adjacent time window

4. query_metrics
   service: checkout-api
   environment: production
   metrics: error_rate, p95_latency_ms, request_rate, cpu_percent
   incident-adjacent time window

5. query_logs
   service: checkout-api
   environment: production
   severity: ERROR
   incident-adjacent time window

6. get_feature_flags
   service: checkout-api
   environment: production

7. get_maintenance_windows
   service: checkout-api
   environment: production
   incident-adjacent time window

8. get_runbook
   runbook_id: RB-CHECKOUT-ERRORS
```

## Evidence collected

- The incident reported checkout HTTP 500 responses and fewer completed orders beginning at 14:10 UTC.
- Checkout error rate rose from 1.1% at 14:05 to 18.4% at 14:10 and 21.2% at 14:15.
- Request traffic and CPU remained comparatively stable, making resource saturation or a traffic surge less likely.
- Deployment `dep-882` completed at 14:05, shortly before the alert, and introduced a billing-country requirement in order mapping.
- Error logs repeatedly reported `billing_country` missing and identified `dep-882`.
- The `checkout_require_billing_country` flag was enabled by `dep-882` at 14:05.
- No checkout maintenance window overlapped the incident.
- The checkout runbook says a rollback may be proposed when timing, logs, and dependency evidence identify the new code path, but production rollback requires human approval.

## Structured final result

```json
{
  "incident_id": "INC-1042",
  "summary": "Production checkout failures began shortly after deployment dep-882 enabled a stricter billing-country mapping path. Error-rate and log evidence identify that new path while traffic and CPU remain stable, making dep-882 the leading cause.",
  "severity": "SEV2",
  "evidence": [
    {
      "source": "get_incident",
      "observation": "INC-1042 reports checkout HTTP 500 responses and reduced completed orders beginning at 2026-07-10T14:10:00Z."
    },
    {
      "source": "query_metrics",
      "observation": "Checkout error rate increased from 1.1% at 14:05 to 18.4% at 14:10 and 21.2% at 14:15 while CPU remained near 45–47%."
    },
    {
      "source": "get_recent_deployments",
      "observation": "Deployment dep-882 completed at 14:05 and introduced a billing-country requirement in order mapping."
    },
    {
      "source": "query_logs",
      "observation": "Repeated checkout errors report a missing billing_country for legacy customer addresses and identify deployment dep-882."
    },
    {
      "source": "get_feature_flags",
      "observation": "checkout_require_billing_country was enabled in production by dep-882 at 14:05."
    },
    {
      "source": "get_maintenance_windows",
      "observation": "No checkout maintenance window overlaps the incident interval."
    },
    {
      "source": "get_runbook",
      "observation": "RB-CHECKOUT-ERRORS permits proposing rollback when timing and logs identify a new checkout code path, but requires human approval for production rollback."
    }
  ],
  "likely_causes": [
    {
      "cause": "A regression introduced by checkout-api deployment dep-882 in the billing-country order-mapping path.",
      "supporting_evidence": [
        "dep-882 completed five minutes before the alert.",
        "Logs identify both the new billing_country validation failure and dep-882.",
        "The related feature flag was enabled by dep-882 at the same time."
      ]
    }
  ],
  "recommended_actions": [
    {
      "action": "Roll back checkout-api deployment dep-882 in production.",
      "rationale": "Deployment timing, repeated error signatures, and the associated feature-flag change consistently identify dep-882 as the likely regression source.",
      "requires_approval": true,
      "approval_action": "rollback_deployment"
    }
  ],
  "confidence": "high",
  "requires_human_approval": true
}
```

The learning version stops at the recommendation. It does not execute the rollback.
