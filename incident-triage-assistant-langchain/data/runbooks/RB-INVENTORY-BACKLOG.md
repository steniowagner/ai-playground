# Inventory Queue Backlog

Owner: Fulfilment  
Applies to: `inventory-worker`  
Last reviewed: 2026-06-24

1. Check queue-depth trend, worker CPU, and processing errors.
2. Determine whether the queue is growing because workers are saturated or unable to access a dependency.
3. For database authentication failures, escalate to the credential owner for rotation; never print or request secret values.
4. Restarting workers does not repair expired credentials and may increase recovery time.
5. Preserve all queued reservation events.
