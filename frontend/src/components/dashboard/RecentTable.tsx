import { useQuery } from "@tanstack/react-query";
import { Eye } from "lucide-react";
import { listItems } from "../../api/client";
import type { ItemRow } from "../../api/types";
import { useNavigate } from "../../lib/router";
import {
  difficultyColor,
  formatDate,
  formatSubject,
  qualityColor,
  statusStyles,
} from "../../lib/format";

export function RecentTable() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["items"],
    queryFn: () => listItems(),
  });

  const rows = (data?.items ?? []).slice(0, 10);

  function openPractice(row: ItemRow) {
    if (row.type.toLowerCase() === "frq") return;
    navigate(`/practice/${row.run_id}`);
  }

  return (
    <section className="rounded-xl border border-slate-100 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-6 py-4">
        <h2 className="text-lg font-semibold text-slate-900">Recent Generations</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-xs font-medium uppercase tracking-wide text-slate-muted">
              <th className="px-6 py-3">Date</th>
              <th className="px-4 py-3">Subject</th>
              <th className="px-4 py-3">Topic</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Difficulty</th>
              <th className="px-4 py-3">Quality</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-slate-muted">
                  Loading…
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-error">
                  Failed to load history.
                </td>
              </tr>
            )}
            {!isLoading && !isError && rows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-slate-muted">
                  No generations yet. Create your first question above.
                </td>
              </tr>
            )}
            {rows.map((row) => {
              const isFrq = row.type.toLowerCase() === "frq";
              return (
                <tr key={row.run_id} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-6 py-3.5 text-slate-700">{formatDate(row.created_at)}</td>
                  <td className="px-4 py-3.5 text-slate-700">{formatSubject(row.subject)}</td>
                  <td className="px-4 py-3.5 capitalize text-slate-700">
                    {row.skill.replace(/-/g, " ")}
                  </td>
                  <td className="px-4 py-3.5 uppercase text-slate-600">{row.type}</td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold ${difficultyColor(row.difficulty)}`}
                    >
                      {row.difficulty}
                    </span>
                  </td>
                  <td className={`px-4 py-3.5 ${qualityColor(row.quality_score)}`}>
                    {row.quality_score ?? "—"}
                  </td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusStyles(row.status)}`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="px-6 py-3.5">
                    <button
                      type="button"
                      onClick={() => openPractice(row)}
                      disabled={isFrq}
                      title={
                        isFrq
                          ? "FRQ practice is not available yet"
                          : "Practice this question"
                      }
                      aria-label={
                        isFrq
                          ? "FRQ practice not available yet"
                          : "Practice question"
                      }
                      className={`rounded-lg p-1.5 ${
                        isFrq
                          ? "cursor-not-allowed text-slate-300"
                          : "text-slate-muted hover:bg-slate-100 hover:text-brand"
                      }`}
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
