from agent.evaluation.report import EvaluationReport


def test_evaluation_report_formats_metrics() -> None:
    report = EvaluationReport(
        total_cases=4,
        hit_at_1=0.25,
        hit_at_3=0.75,
        hit_at_5=1.0,
    )

    formatted = str(report)

    assert "total_cases: 4" in formatted
    assert "hit_at_1: 0.25" in formatted
    assert "hit_at_3: 0.75" in formatted
    assert "hit_at_5: 1.00" in formatted
