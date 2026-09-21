export type SampleQuestion = {
  id: string;
  category: string;
  question: string;
  expected_answer: string;
  tags: string[];
};

export type ToolState = "running" | "finished" | "failed" | "skipped";

export type ActionProposal = {
  proposal_id: string;
  incident_id: string;
  kind: string;
  rationale: string;
  args: Record<string, unknown>;
};

export type InvestigationEvidence = {
  source: string;
  observation: string;
};

export type RecommendedAction = {
  kind: string;
  rationale: string;
  action?: string;
  args?: Record<string, unknown>;
};

export type InvestigationResult = {
  incident_id: string;
  summary: string;
  severity?: string;
  evidence?: InvestigationEvidence[];
  likely_causes?: Array<{ cause: string; supporting_evidence: string[] }>;
  recommended_actions?: RecommendedAction[];
  confidence?: string;
  error_code?: string;
  retryable?: false;
};

export type ConversationItem =
  | { id: string; kind: "user"; content: string }
  | { id: string; kind: "assistant"; content: string }
  | {
      id: string;
      kind: "tool";
      tool: string;
      arguments: Record<string, unknown>;
      state: ToolState;
      detail?: string;
    }
  | { id: string; kind: "result"; result: InvestigationResult }
  | { id: string; kind: "approval"; actions: ActionProposal[] }
  | {
      id: string;
      kind: "proposal";
      proposalId: string;
      actionKind: string;
      state: "executing" | "executed" | "failed" | "rejected";
    }
  | { id: string; kind: "error"; content: string };

export type StreamEvent = {
  event_id: string;
  thread_id: string;
  type: string;
  [key: string]: unknown;
};

export type EvaluationSplit = "development" | "held_out";

export type EvaluationExpectationValue =
  | string
  | number
  | boolean
  | string[]
  | null;

export type EvaluationCase = {
  case_id: string;
  incident_id: string;
  user_request: string;
  fixture_clock: string;
  actor_id: string | null;
  expected: Record<string, EvaluationExpectationValue>;
  tags: string[];
};

export type EvaluationCheck = {
  expectation: string;
  passed: boolean;
  safety: boolean;
  detail: string;
};

export type EvaluationResult = {
  case_id: string;
  observation: Record<string, unknown>;
  score: {
    case_id: string;
    checks: EvaluationCheck[];
    pass_rate: number;
    safety_pass_rate: number;
    passed: boolean;
  };
  event_count: number;
  terminated: boolean;
  run_error: string | null;
  judge_notes: string[];
};
