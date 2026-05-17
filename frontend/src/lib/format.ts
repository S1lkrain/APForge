export const SUBJECT_LABELS: Record<string, string> = {
  ap_precalculus: "AP Precalculus",
};

export const TOPIC_OPTIONS = [
  { value: "limits", label: "Limits" },
  { value: "linear-functions", label: "Linear Functions" },
  { value: "polynomials", label: "Polynomials" },
  { value: "trigonometry", label: "Trigonometry" },
  { value: "exponential-functions", label: "Exponential Functions" },
];

export function formatSubject(subject: string): string {
  return SUBJECT_LABELS[subject] ?? subject;
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatPercent(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function formatDelta(value: number, kind: "count" | "percent" | "score"): string {
  const sign = value >= 0 ? "+" : "";
  if (kind === "percent") {
    return `${sign}${(value * 100).toFixed(1)}% this week`;
  }
  if (kind === "score") {
    return `${sign}${value.toFixed(1)} this week`;
  }
  return `${sign}${value} this week`;
}

export function difficultyColor(level: number): string {
  if (level <= 2) return "bg-emerald-100 text-emerald-700 border-emerald-200";
  if (level === 3) return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-red-100 text-red-700 border-red-200";
}

export function qualityColor(score: number | null): string {
  if (score === null) return "text-slate-muted";
  if (score >= 80) return "text-success font-semibold";
  if (score < 60) return "text-error font-semibold";
  return "text-warn font-semibold";
}

export function statusStyles(status: string): string {
  switch (status) {
    case "Success":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "Warn":
      return "bg-amber-50 text-amber-700 border-amber-200";
    default:
      return "bg-red-50 text-red-700 border-red-200";
  }
}
