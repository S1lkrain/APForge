import type { QueryClient } from "@tanstack/react-query";
import type { GenerateRequest, GenerateResponse, ItemRow, ItemsListResponse } from "../api/types";

export function mapHarnessToUiStatus(finalStatus: string): ItemRow["status"] {
  if (finalStatus === "accepted") return "Success";
  if (finalStatus === "accepted_with_warning") return "Warn";
  return "Rejected";
}

function qualityScoreFromMetrics(metrics: Record<string, unknown>): number | null {
  const judgeScores = metrics.judge_scores;
  if (!judgeScores || typeof judgeScores !== "object") return null;
  const scores = judgeScores as Record<string, unknown>;
  const keys = ["schema_score", "consistency_score", "pedagogy_score", "compliance_score"];
  const values = keys.map((key) => scores[key]).filter((v): v is number => typeof v === "number");
  if (values.length !== keys.length) return null;
  return Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 10) / 10;
}

export function buildItemRowFromGenerate(
  data: GenerateResponse,
  req: GenerateRequest,
): ItemRow {
  return {
    run_id: data.run_id,
    created_at: new Date().toISOString(),
    subject: req.subject,
    skill: req.skill,
    difficulty: req.difficulty,
    type: req.type,
    final_status: data.harness.status,
    status: mapHarnessToUiStatus(data.harness.status),
    quality_score: qualityScoreFromMetrics(data.metrics),
    question: data.item.question,
    choices: data.item.choices,
    answer: data.item.answer,
    explanation: data.item.explanation,
    metadata: data.item.metadata ?? {},
    visual: data.item.visual ?? null,
  };
}

export function upsertItemInCache(
  queryClient: QueryClient,
  row: ItemRow,
): void {
  queryClient.setQueriesData<ItemsListResponse>({ queryKey: ["items", "recent"] }, (old) => {
    if (!old) return old;
    const rest = old.items.filter((item) => item.run_id !== row.run_id);
    return {
      ...old,
      items: [row, ...rest].slice(0, old.page_size),
      total: old.total + (old.items.some((item) => item.run_id === row.run_id) ? 0 : 1),
    };
  });
}
