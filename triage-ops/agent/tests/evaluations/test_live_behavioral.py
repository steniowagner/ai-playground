from __future__ import annotations

import os

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.evaluation.behavioral import (
    BehavioralEvaluationRunner,
    ModelBehavioralJudge,
)
from triage_ops.graph import GraphRunner, build_graph
from triage_ops.model import create_model
from triage_ops.repositories.evaluation_cases import JSONLEvaluationCasesRepository

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.live_model,
    pytest.mark.slow,
    pytest.mark.asyncio,
]

EVALUATION_CASES = JSONLEvaluationCasesRepository()


def live_runner() -> BehavioralEvaluationRunner:
    subject_model = create_model("anthropic")
    judge_model = create_model(
        "anthropic", model_name=os.getenv("ANTHROPIC_EVALUATOR_MODEL")
    )
    graph = build_graph(subject_model, InMemorySaver())
    return BehavioralEvaluationRunner(
        graph_runner=GraphRunner(graph),
        graph=graph,
        judge=ModelBehavioralJudge(judge_model),
    )


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_MODEL_EVALUATIONS") != "1",
    reason="set RUN_LIVE_MODEL_EVALUATIONS=1 to run provider-backed development evaluations",
)
async def test_development_behavior_meets_acceptance_policy() -> None:
    report = await live_runner().run_cases(EVALUATION_CASES.find_all("development"))

    assert report.passed, report.model_dump_json(indent=2)


@pytest.mark.skipif(
    os.getenv("RUN_HELD_OUT_MODEL_EVALUATIONS") != "1",
    reason="set RUN_HELD_OUT_MODEL_EVALUATIONS=1 for final held-out regression only",
)
async def test_held_out_behavior_meets_acceptance_policy() -> None:
    report = await live_runner().run_cases(EVALUATION_CASES.find_all("held_out"))

    assert report.passed, report.model_dump_json(indent=2)
