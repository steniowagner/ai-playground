from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.graph import GraphRunner, build_graph
from triage_ops.model import create_model

from .behavioral import BehavioralEvaluationRunner, ModelBehavioralJudge
from .evaluation import EvaluationCase, load_cases

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS = {
    "development": PROJECT_ROOT / "data" / "evals" / "development.jsonl",
    "held_out": PROJECT_ROOT / "data" / "evals" / "held_out.jsonl",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run provider-backed behavioral evaluations through the real graph."
    )
    parser.add_argument(
        "--split",
        choices=tuple(DATASETS),
        default="development",
        help="Dataset split to run (default: development).",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Run only this case ID; repeat to select more than one case.",
    )
    parser.add_argument(
        "--confirm-held-out",
        action="store_true",
        help="Required for held-out runs to prevent accidental prompt tuning.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=120,
        help="Per-case graph timeout (default: 120).",
    )
    parser.add_argument(
        "--subject-model",
        help="Optional subject model override; defaults to ANTHROPIC_MODEL.",
    )
    parser.add_argument(
        "--evaluator-model",
        help=(
            "Optional judge model override; defaults to ANTHROPIC_EVALUATOR_MODEL "
            "then ANTHROPIC_MODEL."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the complete JSON report.",
    )
    return parser


def select_cases(
    split: Literal["development", "held_out"], case_ids: list[str]
) -> list[EvaluationCase]:
    cases = load_cases(DATASETS[split])
    if not case_ids:
        return cases

    requested = set(case_ids)
    selected = [case for case in cases if case.case_id in requested]
    missing = requested - {case.case_id for case in selected}
    if missing:
        raise ValueError(f"Unknown case IDs: {', '.join(sorted(missing))}")
    return selected


async def run(args: argparse.Namespace) -> int:
    split: Literal["development", "held_out"] = args.split
    if split == "held_out" and not args.confirm_held_out:
        raise ValueError(
            "Held-out evaluation requires --confirm-held-out and must not be used "
            "for prompt tuning."
        )

    cases = select_cases(split, args.case_id)
    subject_model = create_model("anthropic", model_name=args.subject_model)
    judge_model = create_model(
        "anthropic",
        model_name=(args.evaluator_model or os.getenv("ANTHROPIC_EVALUATOR_MODEL")),
    )
    graph = build_graph(subject_model, InMemorySaver())
    runner = BehavioralEvaluationRunner(
        graph_runner=GraphRunner(graph),
        graph=graph,
        judge=ModelBehavioralJudge(judge_model),
        timeout_seconds=args.timeout_seconds,
    )
    report = await runner.run_cases(cases)
    report_json = report.model_dump_json(indent=2)
    print(report_json)

    if args.output is not None:
        args.output.write_text(f"{report_json}\n", encoding="utf-8")

    return 0 if report.passed else 1


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    try:
        exit_code = asyncio.run(run(args))
    except (KeyError, ValueError) as error:
        parser.error(str(error))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
