"use client";

import {
  AlertTriangle,
  ArrowLeft,
  Check,
  ChevronDown,
  Clock3,
  FlaskConical,
  LoaderCircle,
  Play,
  RefreshCcw,
  ShieldCheck,
  X,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  EvaluationCase,
  EvaluationExpectationValue,
  EvaluationResult,
  EvaluationSplit,
} from "@/lib/types";

const API_ROOT = "/api/triage";

const humanize = (value: string) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

const percentage = (value: number) => `${Math.round(value * 100)}%`;

function formatExpectation(value: EvaluationExpectationValue) {
  if (Array.isArray(value)) return value.map(humanize).join(", ");
  if (typeof value === "boolean") return value ? "Required" : "Not required";
  if (typeof value === "string") return humanize(value);
  return String(value);
}

function ResultPanel({ result }: { result: EvaluationResult }) {
  const failedToFinish = !result.terminated || Boolean(result.run_error);
  const passed = result.score.passed && !failedToFinish;

  return (
    <section
      className={`evaluation-result ${passed ? "is-passed" : "is-failed"}`}
      aria-label={`Result for ${result.case_id}`}
    >
      <div className="evaluation-result-summary">
        <div className="evaluation-verdict">
          <span className="evaluation-verdict-icon">
            {passed ? <Check size={17} /> : <X size={17} />}
          </span>
          <div>
            <strong>
              {passed ? "Evaluation passed" : "Evaluation failed"}
            </strong>
            <span>
              {result.event_count} graph events · {result.score.checks.length}{" "}
              checks
            </span>
          </div>
        </div>
        <div className="evaluation-rates">
          <span>
            Quality <strong>{percentage(result.score.pass_rate)}</strong>
          </span>
          <span>
            Safety <strong>{percentage(result.score.safety_pass_rate)}</strong>
          </span>
        </div>
      </div>

      {result.run_error && (
        <div className="evaluation-run-error">
          <AlertTriangle size={15} /> Run ended with{" "}
          {humanize(result.run_error)}.
        </div>
      )}

      <div className="evaluation-checks">
        {result.score.checks.map((check) => (
          <div className="evaluation-check" key={check.expectation}>
            <span className={check.passed ? "check-pass" : "check-fail"}>
              {check.passed ? <Check size={13} /> : <X size={13} />}
            </span>
            <div>
              <strong>{humanize(check.expectation)}</strong>
              <small>{check.detail}</small>
            </div>
            {check.safety && <em>Safety</em>}
          </div>
        ))}
      </div>

      {!!result.judge_notes.length && (
        <details className="judge-notes">
          <summary>
            Evaluator notes <ChevronDown size={14} />
          </summary>
          <ul>
            {result.judge_notes.map((note, index) => (
              <li key={`${note}-${index}`}>{note}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

function EvaluationCard({
  evaluation,
  result,
  error,
  running,
  disabled,
  onRun,
}: {
  evaluation: EvaluationCase;
  result?: EvaluationResult;
  error?: string;
  running: boolean;
  disabled: boolean;
  onRun: () => void;
}) {
  const expectations = Object.entries(evaluation.expected).filter(
    (entry): entry is [string, Exclude<EvaluationExpectationValue, null>] =>
      entry[1] !== null,
  );

  return (
    <article className="evaluation-card">
      <header className="evaluation-card-header">
        <div>
          <span className="evaluation-case-id">{evaluation.case_id}</span>
          <span className="evaluation-incident">{evaluation.incident_id}</span>
        </div>
        <div className="evaluation-tags">
          {evaluation.tags.map((tag) => (
            <span key={tag}>{humanize(tag)}</span>
          ))}
        </div>
      </header>

      <div className="evaluation-card-body">
        <div className="evaluation-request">
          <span>User request</span>
          <p>{evaluation.user_request}</p>
          <small>
            <Clock3 size={13} /> Evidence cutoff {evaluation.fixture_clock}
          </small>
        </div>

        <div className="evaluation-expectations">
          <span>Expected behavior</span>
          <dl>
            {expectations.map(([key, value]) => (
              <div key={key}>
                <dt>{humanize(key)}</dt>
                <dd>{formatExpectation(value)}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="evaluation-card-action">
          <button type="button" onClick={onRun} disabled={disabled}>
            {running ? (
              <>
                <LoaderCircle className="spin" size={16} /> Running evaluation
              </>
            ) : (
              <>
                <Play size={15} /> {result ? "Run again" : "Run evaluation"}
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="evaluation-api-error" role="alert">
            <AlertTriangle size={15} /> {error}
          </div>
        )}
        {result && <ResultPanel result={result} />}
      </div>
    </article>
  );
}

export function EvaluationWorkspace() {
  const [split, setSplit] = useState<EvaluationSplit>("development");
  const [cases, setCases] = useState<EvaluationCase[]>([]);
  const [results, setResults] = useState<Record<string, EvaluationResult>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [runningCaseId, setRunningCaseId] = useState<string | null>(null);

  const loadCases = useCallback(
    async (activeSplit: EvaluationSplit, signal?: AbortSignal) => {
      setLoading(true);
      setListError(null);
      try {
        const response = await fetch(
          `${API_ROOT}/evaluations?split=${activeSplit}`,
          { cache: "no-store", signal },
        );
        const payload = (await response.json()) as
          | EvaluationCase[]
          | { detail?: string };
        if (!response.ok || !Array.isArray(payload)) {
          throw new Error(
            !Array.isArray(payload) && payload.detail
              ? payload.detail
              : "Could not load evaluation cases.",
          );
        }
        setCases(payload);
      } catch (error) {
        if (signal?.aborted) return;
        setCases([]);
        setListError(
          error instanceof Error
            ? error.message
            : "Could not load evaluation cases.",
        );
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadCases(split, controller.signal);
    return () => controller.abort();
  }, [loadCases, split]);

  const completedCount = useMemo(
    () => cases.filter((evaluation) => results[evaluation.case_id]).length,
    [cases, results],
  );

  const passedCount = useMemo(
    () =>
      cases.filter((evaluation) => results[evaluation.case_id]?.score.passed)
        .length,
    [cases, results],
  );

  const runCase = useCallback(
    async (evaluation: EvaluationCase) => {
      if (runningCaseId) return;

      const heldOut = evaluation.case_id.startsWith("holdout-");
      if (
        heldOut &&
        !window.confirm(
          "Held-out evaluations are for final regression checks only. Continue with this run?",
        )
      ) {
        return;
      }

      setRunningCaseId(evaluation.case_id);
      setErrors((current) => {
        const next = { ...current };
        delete next[evaluation.case_id];
        return next;
      });

      try {
        const query = heldOut ? "?confirm_held_out=true" : "";
        const response = await fetch(
          `${API_ROOT}/evaluations/${evaluation.case_id}/run${query}`,
          { method: "POST" },
        );
        const payload = (await response.json()) as
          | EvaluationResult
          | { detail?: string };
        if (!response.ok || !("score" in payload)) {
          throw new Error(
            "detail" in payload && payload.detail
              ? payload.detail
              : "The evaluation could not be completed.",
          );
        }
        setResults((current) => ({
          ...current,
          [evaluation.case_id]: payload,
        }));
      } catch (error) {
        setErrors((current) => ({
          ...current,
          [evaluation.case_id]:
            error instanceof Error
              ? error.message
              : "The evaluation could not be completed.",
        }));
      } finally {
        setRunningCaseId(null);
      }
    },
    [runningCaseId],
  );

  return (
    <main className="app-shell evaluation-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <Image
              src="/triageops-radar.png"
              alt=""
              width={36}
              height={36}
              priority
            />
          </div>
          <div>
            <strong>TriageOps</strong>
            <span>MODEL EVALUATIONS</span>
          </div>
        </div>
        <div className="topbar-meta">
          <Link className="topbar-link" href="/">
            <ArrowLeft size={15} /> Incident workspace
          </Link>
        </div>
      </header>

      <div className="evaluation-page">
        <section className="evaluation-hero">
          <div>
            <span className="eyebrow">
              <FlaskConical size={14} /> Quality control
            </span>
            <h1>Behavioral evaluations</h1>
            <p>
              Run curated incident scenarios through the complete graph and
              compare the final behavior with explicit quality and safety
              requirements.
            </p>
          </div>
          <div className="evaluation-overview">
            <div>
              <span>Cases</span>
              <strong>{loading ? "—" : cases.length}</strong>
            </div>
            <div>
              <span>Completed</span>
              <strong>{completedCount}</strong>
            </div>
            <div>
              <span>Passed</span>
              <strong>{passedCount}</strong>
            </div>
          </div>
        </section>

        <section className="evaluation-toolbar" aria-label="Evaluation dataset">
          <div className="evaluation-split-control">
            <div className="split-switcher">
              <button
                className={split === "development" ? "is-active" : ""}
                type="button"
                onClick={() => setSplit("development")}
                disabled={Boolean(runningCaseId)}
              >
                Development
              </button>
              <button
                className={split === "held_out" ? "is-active" : ""}
                type="button"
                onClick={() => setSplit("held_out")}
                disabled={Boolean(runningCaseId)}
              >
                Held-out
              </button>
            </div>
            <p className="evaluation-split-description">
              {split === "development" ? (
                <span>
                  <strong>Development evaluations</strong> are visible test
                  cases for iterating on prompts and agent behavior. Run them
                  freely while developing.
                </span>
              ) : (
                <span>
                  <strong>Held-out evaluations</strong> are reserved for final
                  regression checks. Avoid using their results to tune prompts
                  or implementation.
                </span>
              )}
            </p>
          </div>
          <aside className="evaluation-grading-note">
            <FlaskConical size={16} />
            <div>
              <strong>How scoring works</strong>
              <span>The final output is graded after the graph finishes.</span>
            </div>
          </aside>
        </section>

        {listError && (
          <section className="evaluation-list-error" role="alert">
            <AlertTriangle size={18} />
            <div>
              <strong>Evaluations are unavailable</strong>
              <span>{listError}</span>
            </div>
            <button type="button" onClick={() => void loadCases(split)}>
              <RefreshCcw size={14} /> Retry
            </button>
          </section>
        )}

        <section className="evaluation-list" aria-live="polite">
          {loading &&
            [1, 2, 3].map((item) => (
              <div
                className="evaluation-card evaluation-card-skeleton"
                key={item}
              />
            ))}
          {!loading &&
            cases.map((evaluation) => (
              <EvaluationCard
                key={evaluation.case_id}
                evaluation={evaluation}
                result={results[evaluation.case_id]}
                error={errors[evaluation.case_id]}
                running={runningCaseId === evaluation.case_id}
                disabled={Boolean(runningCaseId)}
                onRun={() => void runCase(evaluation)}
              />
            ))}
          {!loading && !listError && !cases.length && (
            <div className="evaluation-empty">
              <ShieldCheck size={22} /> No cases are available in this dataset.
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
