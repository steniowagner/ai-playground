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
