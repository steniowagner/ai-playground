from __future__ import annotations

import os
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.graph import GraphRunner, build_graph
from triage_ops.model import create_model

from .behavioral import BehavioralEvaluationRunner, ModelBehavioralJudge
from .evaluation import load_cases

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.live_model,
    pytest.mark.slow,
    pytest.mark.asyncio,
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEVELOPMENT_DATASET = PROJECT_ROOT / "data" / "evals" / "development.jsonl"
HELD_OUT_DATASET = PROJECT_ROOT / "data" / "evals" / "held_out.jsonl"


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
    report = await live_runner().run_cases(load_cases(DEVELOPMENT_DATASET))

    assert report.passed, report.model_dump_json(indent=2)


@pytest.mark.skipif(
    os.getenv("RUN_HELD_OUT_MODEL_EVALUATIONS") != "1",
    reason="set RUN_HELD_OUT_MODEL_EVALUATIONS=1 for final held-out regression only",
)
async def test_held_out_behavior_meets_acceptance_policy() -> None:
    report = await live_runner().run_cases(load_cases(HELD_OUT_DATASET))

    assert report.passed, report.model_dump_json(indent=2)
