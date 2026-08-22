from agent.evaluation.report import EvaluationReport
from agent.evaluation.retrieval import service as service_module
from agent.evaluation.retrieval.cases import RetrievalEvaluationCase
from agent.evaluation.retrieval.evaluation import RetrievalEvaluation
from agent.evaluation.retrieval.service import RetrievalEvaluationService


class FakeEmbedder:
    pass


class FakeRepository:
    pass


class FakeRetrievalService:
    def __init__(self, embedder, repository) -> None:
        self.embedder = embedder
        self.repository = repository


class FakeRetrievalEvaluator:
    instances: list["FakeRetrievalEvaluator"] = []

    def __init__(self, retrieval_service) -> None:
        self.retrieval_service = retrieval_service
        self.cases: list[RetrievalEvaluationCase] = []
        self.__class__.instances.append(self)

    def evaluate(self, case: RetrievalEvaluationCase) -> RetrievalEvaluation:
        self.cases.append(case)
        return RetrievalEvaluation(
            question=case.question,
            retrieved_sources=list(case.expected_sources),
            expected_sources=case.expected_sources,
            is_correct=True,
        )


def test_evaluate_retrieval_evaluates_all_cases_and_builds_report(
    monkeypatch,
) -> None:
    cases = [
        RetrievalEvaluationCase("first question", {"first.md"}),
        RetrievalEvaluationCase("second question", {"second.md"}),
    ]
    expected_report = EvaluationReport(2, 1.0, 1.0, 1.0)
    report_inputs: list[list[RetrievalEvaluation]] = []
    FakeRetrievalEvaluator.instances = []

    def fake_build_report(evaluations: list[RetrievalEvaluation]) -> EvaluationReport:
        report_inputs.append(evaluations)
        return expected_report

    monkeypatch.setattr(service_module, "RETRIEVAL_EVALUATION_CASES", cases)
    monkeypatch.setattr(
        service_module,
        "RetrievalService",
        FakeRetrievalService,
    )
    monkeypatch.setattr(
        service_module,
        "RetrievalEvaluator",
        FakeRetrievalEvaluator,
    )
    monkeypatch.setattr(
        service_module,
        "build_retrieval_evaluation_report",
        fake_build_report,
    )
    embedder = FakeEmbedder()
    repository = FakeRepository()

    service = RetrievalEvaluationService(
        embedder,  # type: ignore[arg-type]
        repository,  # type: ignore[arg-type]
    )
    report = service.evaluate_retrieval()

    assert report is expected_report
    assert len(FakeRetrievalEvaluator.instances) == 1
    evaluator = FakeRetrievalEvaluator.instances[0]
    assert evaluator.cases == cases
    assert len(report_inputs) == 1
    assert [evaluation.question for evaluation in report_inputs[0]] == [
        "first question",
        "second question",
    ]
