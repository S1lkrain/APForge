import { useQuery } from "@tanstack/react-query";
import { Activity, BarChart2, CheckCircle2, Sparkles } from "lucide-react";
import { getStats } from "../../api/client";
import { formatDelta, formatPercent } from "../../lib/format";

const cards = [
  {
    key: "total_generated" as const,
    label: "Total Generated",
    icon: Sparkles,
    iconBg: "bg-emerald-100 text-emerald-600",
    deltaKind: "count" as const,
    deltaColor: "text-emerald-600",
  },
  {
    key: "success_rate" as const,
    label: "Success Rate",
    icon: CheckCircle2,
    iconBg: "bg-blue-100 text-brand",
    deltaKind: "percent" as const,
    deltaColor: "text-brand",
  },
  {
    key: "avg_quality_score" as const,
    label: "Avg. Quality Score",
    icon: BarChart2,
    iconBg: "bg-amber-100 text-warn",
    deltaKind: "score" as const,
    deltaColor: "text-warn",
  },
  {
    key: "total_runs" as const,
    label: "Total Runs",
    icon: Activity,
    iconBg: "bg-violet-100 text-accent-purple",
    deltaKind: "count" as const,
    deltaColor: "text-accent-purple",
  },
];

export function StatCards() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.key}
            className="h-28 animate-pulse rounded-xl border border-slate-100 bg-white"
          />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-error">
        Could not load statistics. Is the API running?
      </p>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        const value = data[card.key];
        const delta = data.week_delta[card.key];
        let display = String(value);
        if (card.key === "success_rate") {
          display = formatPercent(value as number);
        } else if (card.key === "avg_quality_score") {
          display = (value as number).toFixed(1);
        }

        return (
          <article
            key={card.key}
            className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-muted">{card.label}</p>
                <p className="mt-2 text-3xl font-bold text-slate-900">{display}</p>
                <p className={`mt-1 text-xs font-medium ${card.deltaColor}`}>
                  {formatDelta(delta, card.deltaKind)}
                </p>
              </div>
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full ${card.iconBg}`}
              >
                <Icon className="h-5 w-5" />
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
