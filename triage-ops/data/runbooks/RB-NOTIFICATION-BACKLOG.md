# Notification Queue Backlog

Owner: Customer Comms  
Applies to: `notification-worker`  
Last reviewed: 2026-06-25

1. Confirm queue depth trend and worker error rate.
2. Check whether CPU is saturated or workers are idle/failing.
3. Inspect deployments from the prior 60 minutes.
4. Sample errors for connection-pool, provider-rate-limit, or malformed-job patterns.
5. When a new deployment introduced repeatable connection-pool failures, propose rollback of that exact deployment.

Production rollbacks require approval. Do not purge the queue; queued notifications must be preserved.
