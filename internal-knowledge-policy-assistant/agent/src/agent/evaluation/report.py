from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationReport:
    total_cases: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float