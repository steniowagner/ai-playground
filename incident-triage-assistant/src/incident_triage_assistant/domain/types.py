from typing import Literal

Environment = Literal["production", "staging"]

ServiceMetric = Literal[
    "error_rate",
    "p95_latency_ms",
    "request_rate",
    "cpu_percent",
    "queue_depth",
]
