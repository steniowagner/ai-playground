"use client";

import {
  AlertTriangle,
  ArrowUp,
  Bot,
  Check,
  ChevronRight,
  CircleDot,
  FileSearch,
  FlaskConical,
  LoaderCircle,
  RotateCcw,
  ServerCog,
  ShieldCheck,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { MarkdownText } from "@/components/markdown-text";
import { consumeEventStream } from "@/lib/sse";
import type {
  ActionProposal,
  ConversationItem,
  InvestigationResult,
  SampleQuestion,
  StreamEvent,
} from "@/lib/types";

const API_ROOT = "/api/triage";

const humanize = (value: string) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

const shortThread = (threadId: string | null) =>
  threadId ? threadId.split("-")[0].toUpperCase() : "STARTING";

function StatusPill({ online, busy }: { online: boolean; busy: boolean }) {
  const label = busy
    ? "Agent working"
    : online
      ? "API connected"
      : "API offline";
  return (
    <div className={`status-pill ${online ? "is-online" : "is-offline"}`}>
      <span className="status-dot" />
      {label}
    </div>
  );
}

function ToolActivity({
  item,
}: {
  item: Extract<ConversationItem, { kind: "tool" }>;
}) {
  const Icon =
    item.state === "running"
      ? LoaderCircle
      : item.state === "finished"
        ? Check
        : AlertTriangle;
  return (
    <div className={`tool-activity state-${item.state}`}>
      <div className="tool-icon">
        <Icon size={15} className={item.state === "running" ? "spin" : ""} />
      </div>
      <div>
        <p>{humanize(item.tool)}</p>
        <span>
          {item.state === "running"
            ? "Querying operational data"
            : humanize(item.detail ?? item.state)}
        </span>
      </div>
    </div>
  );
}

function InvestigationCard({ result }: { result: InvestigationResult }) {
  const failed = Boolean(result.error_code);
  return (
    <article className={`investigation-card ${failed ? "is-failure" : ""}`}>
      <header>
        <div>
          <div className="eyebrow">
            <FileSearch size={14} /> Investigation complete
          </div>
          <h2>{result.incident_id}</h2>
        </div>
        {result.severity && (
          <span className={`severity ${result.severity.toLowerCase()}`}>
            {result.severity}
          </span>
        )}
      </header>

      <MarkdownText className="result-summary">{result.summary}</MarkdownText>

      {!failed && (
        <>
          <div className="result-meta">
            <span>
              <ShieldCheck size={15} />{" "}
              {humanize(result.confidence ?? "unknown")} confidence
            </span>
            <span>
              <CircleDot size={15} /> {result.evidence?.length ?? 0} evidence
              points
            </span>
          </div>

          {!!result.likely_causes?.length && (
            <section className="result-section">
              <h3>Likely cause</h3>
              {result.likely_causes.map((cause, index) => (
                <div className="cause-row" key={`${cause.cause}-${index}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <MarkdownText>{cause.cause}</MarkdownText>
                </div>
              ))}
            </section>
          )}

          {!!result.evidence?.length && (
            <details className="evidence-details">
              <summary>
                View evidence trail <ChevronRight size={15} />
              </summary>
              <div>
                {result.evidence.map((evidence, index) => (
                  <div
                    className="evidence-row"
                    key={`${evidence.source}-${index}`}
                  >
                    <code>{humanize(evidence.source)}</code>
                    <MarkdownText>{evidence.observation}</MarkdownText>
                  </div>
                ))}
              </div>
            </details>
          )}

          {!!result.recommended_actions?.length && (
            <section className="result-section recommended-actions">
              <h3>Recommended actions</h3>
              {result.recommended_actions.map((action, index) => (
                <div className="action-row" key={`${action.kind}-${index}`}>
                  <Zap size={14} />
                  <div>
                    <strong>{humanize(action.kind)}</strong>
                    <MarkdownText>
                      {action.action ?? action.rationale}
                    </MarkdownText>
                  </div>
                </div>
              ))}
            </section>
          )}
        </>
      )}
    </article>
  );
}

function ApprovalCard({
  item,
  disabled,
  onSubmit,
}: {
  item: Extract<ConversationItem, { kind: "approval" }>;
  disabled: boolean;
  onSubmit: (
    actions: ActionProposal[],
    decisions: Record<string, boolean>,
  ) => void;
}) {
  const [decisions, setDecisions] = useState<Record<string, boolean>>({});
  const [submitted, setSubmitted] = useState(false);
  const ready = item.actions.every(
    (action) => typeof decisions[action.proposal_id] === "boolean",
  );

  return (
    <article className="approval-card">
      <div className="approval-heading">
        <div className="approval-mark">
          <ShieldCheck size={19} />
        </div>
        <div>
          <span>Human checkpoint</span>
          <h3>Review proposed actions</h3>
        </div>
      </div>
      <p className="approval-intro">
        Nothing changes until you explicitly approve it.
      </p>

      {item.actions.map((action) => (
        <div className="proposal" key={action.proposal_id}>
          <div className="proposal-title">
            <Zap size={15} />
            <strong>{humanize(action.kind)}</strong>
            <span>{action.incident_id}</span>
          </div>
          <MarkdownText>{action.rationale}</MarkdownText>
          <dl>
            {Object.entries(action.args).map(([key, value]) => (
              <div key={key}>
                <dt>{humanize(key)}</dt>
                <dd>
                  {typeof value === "string" ? (
                    <MarkdownText>{value}</MarkdownText>
                  ) : (
                    String(value)
                  )}
                </dd>
              </div>
            ))}
          </dl>
          <div
            className="decision-row"
            aria-label={`Decision for ${humanize(action.kind)}`}
          >
            <button
              className={
                decisions[action.proposal_id] === true ? "selected approve" : ""
              }
              disabled={submitted || disabled}
              onClick={() =>
                setDecisions((current) => ({
                  ...current,
                  [action.proposal_id]: true,
                }))
              }
              type="button"
            >
              <Check size={15} /> Approve
            </button>
            <button
              className={
                decisions[action.proposal_id] === false ? "selected reject" : ""
              }
              disabled={submitted || disabled}
              onClick={() =>
                setDecisions((current) => ({
                  ...current,
                  [action.proposal_id]: false,
                }))
              }
              type="button"
            >
              <X size={15} /> Reject
            </button>
          </div>
        </div>
      ))}

      <button
        className="submit-decisions"
        disabled={!ready || disabled || submitted}
        onClick={() => {
          setSubmitted(true);
          onSubmit(item.actions, decisions);
        }}
        type="button"
      >
        {submitted ? "Decisions submitted" : "Submit decisions"}{" "}
        {submitted ? <Check size={16} /> : <ArrowUp size={16} />}
      </button>
    </article>
  );
}

function ConversationFeed({
  items,
  busy,
  onApproval,
}: {
  items: ConversationItem[];
  busy: boolean;
  onApproval: (
    actions: ActionProposal[],
    decisions: Record<string, boolean>,
  ) => void;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items, busy]);

  if (!items.length) {
    return (
      <div className="empty-state">
        <div className="radar">
          <span />
          <span />
          <Bot size={24} />
        </div>
        <div className="eyebrow">Operations copilot</div>
        <h2>What should we investigate?</h2>
        <p>
          Ask an operational question, or investigate an incident using its
          exact ID, such as <code>INC-1042</code>.
        </p>
      </div>
    );
  }

  return (
    <div className="conversation-feed" aria-live="polite">
      {items.map((item) => {
        if (item.kind === "user")
          return (
            <MarkdownText className="message user-message" key={item.id}>
              {item.content}
            </MarkdownText>
          );
        if (item.kind === "assistant")
          return (
            <div className="assistant-row" key={item.id}>
              <div className="assistant-avatar">
                <Sparkles size={15} />
              </div>
              <MarkdownText className="message assistant-message">
                {item.content}
              </MarkdownText>
            </div>
          );
        if (item.kind === "tool")
          return <ToolActivity item={item} key={item.id} />;
        if (item.kind === "result")
          return <InvestigationCard result={item.result} key={item.id} />;
        if (item.kind === "approval")
          return (
            <ApprovalCard
              item={item}
              disabled={busy}
              onSubmit={onApproval}
              key={item.id}
            />
          );
        if (item.kind === "proposal")
          return (
            <div className={`proposal-status is-${item.state}`} key={item.id}>
              {item.state === "executing" ? (
                <LoaderCircle className="spin" size={15} />
              ) : item.state === "rejected" ? (
                <X size={15} />
              ) : (
                <Check size={15} />
              )}
              <span>
                <strong>{humanize(item.actionKind)}</strong>{" "}
                {humanize(item.state)}
              </span>
            </div>
          );
        return (
          <div className="stream-error" key={item.id}>
            <AlertTriangle size={16} />
            <MarkdownText>{item.content}</MarkdownText>
          </div>
        );
      })}
      {busy && (
        <div className="working-indicator">
          <span />
          <span />
          <span />
          <em>Analyzing operational signals</em>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}

export function TriageWorkspace() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [online, setOnline] = useState(false);
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState("");
  const [items, setItems] = useState<ConversationItem[]>([]);
  const [questions, setQuestions] = useState<SampleQuestion[]>([]);
  const [questionError, setQuestionError] = useState(false);
  const assistantMessageId = useRef<string | null>(null);

  const createThread = useCallback(async () => {
    setOnline(false);
    const response = await fetch(`${API_ROOT}/threads`, { method: "POST" });
    if (!response.ok)
      throw new Error("Could not start an investigation thread.");
    const payload = (await response.json()) as { thread_id: string };
    setThreadId(payload.thread_id);
    setOnline(true);
    return payload.thread_id;
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([
      createThread(),
      fetch(`${API_ROOT}/sample-questions`, { cache: "no-store" })
        .then(async (response) => {
          if (!response.ok) throw new Error();
          return response.json() as Promise<{ questions: SampleQuestion[] }>;
        })
        .then((payload) => active && setQuestions(payload.questions))
        .catch(() => active && setQuestionError(true)),
    ]).catch(() => {
      if (active) setOnline(false);
    });
    return () => {
      active = false;
    };
  }, [createThread]);

  const handleEvent = useCallback((event: StreamEvent) => {
    const id = event.event_id ?? crypto.randomUUID();

    if (event.type === "message_chunk") {
      const content = String(event.content ?? "");
      const existingId = assistantMessageId.current;

      if (existingId) {
        setItems((current) =>
          current.map((item) =>
            item.id === existingId && item.kind === "assistant"
              ? { ...item, content: item.content + content }
              : item,
          ),
        );
      } else {
        assistantMessageId.current = id;
        setItems((current) => [...current, { id, kind: "assistant", content }]);
      }

      return;
    }

    if (event.type === "model_thinking") return;
    assistantMessageId.current = null;

    if (event.type === "tool_started") {
      setItems((current) => [
        ...current,
        {
          id,
          kind: "tool",
          tool: String(event.tool),
          arguments: (event.arguments ?? {}) as Record<string, unknown>,
          state: "running",
        },
      ]);
      return;
    }

    if (["tool_finished", "tool_failed", "tool_skipped"].includes(event.type)) {
      const tool = String(event.tool);
      const state =
        event.type === "tool_finished"
          ? "finished"
          : event.type === "tool_failed"
            ? "failed"
            : "skipped";
      setItems((current) => {
        const index = [...current]
          .reverse()
          .findIndex(
            (item) =>
              item.kind === "tool" &&
              item.tool === tool &&
              item.state === "running",
          );
        if (index < 0) return current;
        const actualIndex = current.length - 1 - index;
        return current.map((item, itemIndex) =>
          itemIndex === actualIndex && item.kind === "tool"
            ? {
                ...item,
                state,
                detail: String(
                  event.error_code ??
                    event.reason ??
                    (event.ok === false ? "failed" : "complete"),
                ),
              }
            : item,
        );
      });
      return;
    }

    if (event.type === "investigation_completed") {
      setItems((current) => [
        ...current,
        { id, kind: "result", result: event.result as InvestigationResult },
      ]);
      return;
    }

    if (event.type === "approval_required") {
      setItems((current) => [
        ...current,
        { id, kind: "approval", actions: event.actions as ActionProposal[] },
      ]);
      return;
    }

    if (
      [
        "executing_proposal",
        "proposal_execution_finished",
        "proposal_rejected",
      ].includes(event.type)
    ) {
      const result = event.result as { ok?: boolean } | null;
      const state =
        event.type === "executing_proposal"
          ? "executing"
          : event.type === "proposal_rejected"
            ? "rejected"
            : result?.ok
              ? "executed"
              : "failed";
      const proposalId = String(event.proposal_id);
      const actionKind = String(event.kind);
      setItems((current) => {
        const existing = current.findIndex(
          (item) => item.kind === "proposal" && item.proposalId === proposalId,
        );

        if (existing < 0) {
          return [
            ...current,
            { id, kind: "proposal", proposalId, actionKind, state },
          ];
        }

        return current.map((item, index) =>
          index === existing && item.kind === "proposal"
            ? { ...item, actionKind, state }
            : item,
        );
      });
    }
  }, []);

  const stream = useCallback(
    async (url: string, body: unknown) => {
      setBusy(true);
      assistantMessageId.current = null;
      try {
        await consumeEventStream(url, body, handleEvent);
        setOnline(true);
      } catch (error) {
        setOnline(false);
        setItems((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            kind: "error",
            content:
              error instanceof Error
                ? error.message
                : "The stream was interrupted.",
          },
        ]);
      } finally {
        setBusy(false);
        assistantMessageId.current = null;
      }
    },
    [handleEvent],
  );

  const sendMessage = useCallback(
    async (message: string) => {
      const value = message.trim();
      if (!value || busy) return;
      setInput("");
      setItems((current) => [
        ...current,
        { id: crypto.randomUUID(), kind: "user", content: value },
      ]);

      try {
        const activeThread = threadId ?? (await createThread());
        await stream(`${API_ROOT}/threads/${activeThread}/messages/stream`, {
          message: value,
        });
      } catch (error) {
        setItems((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            kind: "error",
            content:
              error instanceof Error
                ? error.message
                : "Unable to send the message.",
          },
        ]);
      }
    },
    [busy, createThread, stream, threadId],
  );

  const submitApprovals = useCallback(
    async (actions: ActionProposal[], decisions: Record<string, boolean>) => {
      if (!threadId || busy) return;
      await stream(`${API_ROOT}/threads/${threadId}/approvals/stream`, {
        decisions: actions.map((action) => ({
          proposal_id: action.proposal_id,
          approved: decisions[action.proposal_id],
        })),
      });
    },
    [busy, stream, threadId],
  );

  const reset = useCallback(async () => {
    if (busy) return;
    setItems([]);
    setInput("");
    assistantMessageId.current = null;
    try {
      await createThread();
    } catch {
      setOnline(false);
    }
  }, [busy, createThread]);

  const groupedQuestions = useMemo(() => questions, [questions]);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void sendMessage(input);
  };

  return (
    <main className="app-shell">
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
            <span>INCIDENT RESPONSE</span>
          </div>
        </div>
        <div className="topbar-meta">
          <Link className="topbar-link" href="/evaluations">
            <FlaskConical size={15} /> Evaluations
          </Link>
          <button
            className="icon-button"
            type="button"
            onClick={reset}
            disabled={busy}
            aria-label="Start a new session"
            title="Start a new session"
          >
            <RotateCcw size={17} />
          </button>
        </div>
      </header>

      <div className="workspace-grid">
        <section className="chat-panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Live incident workspace</span>
              <h1>Incident triage</h1>
            </div>
          </div>

          <div className="conversation-scroll">
            <ConversationFeed
              items={items}
              busy={busy}
              onApproval={submitApprovals}
            />
          </div>

          <form className="composer" onSubmit={onSubmit}>
            <textarea
              aria-label="Message the triage agent"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Ask about an incident, service, deployment, or operational signal…"
              rows={1}
              disabled={busy}
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              aria-label="Send message"
            >
              {busy ? (
                <LoaderCircle className="spin" size={18} />
              ) : (
                <ArrowUp size={18} />
              )}
            </button>
            <div className="composer-hint">
              <span>Enter to send</span>
              <span>Shift + Enter for a new line</span>
            </div>
          </form>
        </section>

        <aside className="side-panel">
          <div className="scope-card">
            <div>
              <ServerCog size={17} />
              <strong>Operational scope</strong>
            </div>
            <p>
              Incidents · services · deployments · logs · metrics · flags ·
              maintenance · runbooks
            </p>
          </div>

          <div className="side-heading">
            <div>
              <h2>Suggested prompts</h2>
            </div>
            <span>{questions.length || "—"}</span>
          </div>
          <p>Use a sample request to explore the triage workflow.</p>

          <nav className="question-list" aria-label="Sample questions">
            {groupedQuestions.map((question, index) => (
              <button
                key={question.id}
                type="button"
                onClick={() => void sendMessage(question.question)}
                disabled={busy}
              >
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <small>{question.category}</small>
                  <p>{question.question}</p>
                </div>
                <ChevronRight size={16} />
              </button>
            ))}
            {!questions.length &&
              !questionError &&
              [1, 2, 3].map((item) => (
                <div className="question-skeleton" key={item} />
              ))}
            {questionError && (
              <div className="list-error">
                <AlertTriangle size={15} /> Sample questions are unavailable.
              </div>
            )}
          </nav>
        </aside>
      </div>
    </main>
  );
}
