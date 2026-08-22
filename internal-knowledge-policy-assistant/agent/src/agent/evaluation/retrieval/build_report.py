from agent.evaluation.report import EvaluationReport

from .evaluation import RetrievalEvaluation
from .hit import calculate_hit_rate


def build_retrieval_evaluation_report(
    evaluations: list[RetrievalEvaluation],
) -> EvaluationReport:
    return EvaluationReport(
        total_cases=len(evaluations),
        hit_at_1=calculate_hit_rate(evaluations, 1),
        hit_at_3=calculate_hit_rate(evaluations, 3),
        hit_at_5=calculate_hit_rate(evaluations, 5),
    )
