# Web Gateway 5xx Responses

Owner: Edge Platform  
Applies to: `web-gateway`  
Last reviewed: 2026-06-28

1. Identify affected routes and upstream services from bounded trace samples.
2. Compare gateway health with each implicated upstream.
3. Check recent gateway and upstream deployments.
4. If failures span multiple upstreams without a common signal, label the cause unknown and escalate for additional distributed traces.
5. Do not assign a root cause from a small sample alone.
