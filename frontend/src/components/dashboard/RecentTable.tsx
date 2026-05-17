import { useQuery } from "@tanstack/react-query";
import { Eye } from "lucide-react";
import { useState } from "react";
import { listItems } from "../../api/client";
import type { ItemRow } from "../../api/types";
import {
  difficultyColor,
  formatDate,
  formatSubject,
  qualityColor,
  statusStyles,
} from "../../lib/format";

function ItemDetailModal({ item, onClose }: { item: ItemRow; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="item-detail-title"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h3 id="item-detail-title" className="text-lg font-semibold text-slate-900">
            Question detail
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-sm text-slate-muted hover:bg-slate-100"
          >
            Close
          </button>
        </div>
        <p className="mb-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
          {item.question}
        </p>
        {item.choices.length > 0 && (
          <ul className="mb-4 space-y-2">
            {item.choices.map((choice) => (
              <li
                key={choice}
                className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm"
              >
                {choice}
              </li>
            ))}
          </ul>
        )}
        <p className="text-sm">
          <span className="font-medium text-slate-700">Answer: </span>
          {item.answer}
        </p>
        <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">
          {item.explanation}
        </p>
      </div>
    </div>
  );
}

export function RecentTable() {
  const [selected, setSelected] = useState<ItemRow | null>(null);
  const { data, isLoading, isError } = useQuery({
    queryKey: ["items"],
    queryFn: () => listItems(),
  });

  const rows = (data?.items ?? []).slice(0, 10);

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
            {rows.map((row) => (
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
                    onClick={() => setSelected(row)}
                    className="rounded-lg p-1.5 text-slate-muted hover:bg-slate-100 hover:text-brand"
                    aria-label="View question"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && <ItemDetailModal item={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}
