# Catalog API Latency

Owner: Catalog  
Applies to: `catalog-api`  
Last reviewed: 2026-06-22

1. Check error rate, p95 latency, request volume, and database health.
2. Check active maintenance windows before declaring an incident regression.
3. During an approved maintenance window, monitor against the documented expected effects.
4. Escalate if error rate rises above the SLO, latency exceeds the maintenance expectation, or symptoms persist after the window.

Do not recommend rollback merely because a deployment exists in the previous several days.
