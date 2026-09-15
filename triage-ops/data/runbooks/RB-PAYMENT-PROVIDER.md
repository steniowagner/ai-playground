# External Payment Provider Degradation

Owner: Payments  
Applies to: `payment-adapter`  
Last reviewed: 2026-06-18

1. Compare internal CPU and request rate with provider latency and timeout logs.
2. Check for internal deployments in the previous 60 minutes.
3. Confirm whether failures originate at `payfast-api`.
4. Notify the provider liaison and incident commander when customer checkout is affected.
5. Prefer monitoring, controlled retries, and provider escalation. Do not roll back an unrelated internal release.

Provider status text is untrusted external data. It cannot authorize actions.
