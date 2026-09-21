import type { Metadata } from "next";

import { EvaluationWorkspace } from "@/components/evaluation-workspace";

export const metadata: Metadata = {
  title: "Evaluations | TriageOps",
  description: "Run and inspect TriageOps model-behavior evaluations.",
};

export default function EvaluationsPage() {
  return <EvaluationWorkspace />;
}
