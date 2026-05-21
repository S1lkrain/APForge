import { Eye, Trash2 } from "lucide-react";
import type { ItemRow } from "../../api/types";
import {
  difficultyColor,
  formatDateTime,
  formatSubject,
  qualityColor,
  statusStyles,
} from "../../lib/format";
import { Skeleton } from "../ui/Skeleton";

interface GenerationsTableProps {
  rows: ItemRow[];
  isLoading?: boolean;
  isError?: boolean;
  emptyMessage?: string;
  showDelete?: boolean;
  onView?: (row: ItemRow) => void;
  onDelete?: (row: ItemRow) => void;
  deletingRunId?: string | null;
}

export function GenerationsTable({
  rows,
  isLoading = false,
  isError = false,
  emptyMessage = "No generations found.",
  showDelete = false,
  onView,
  onDelete,
  deletingRunId = null,
}: GenerationsTableProps) {
  const skeletonRows = Array.from({ length: 5 }, (_, i) => i);

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[800px] text-left text-sm">
        <caption className="sr-only">Generation history</caption>
        <thead>
          <tr className="border-b border-slate-100 text-xs font-medium uppercase tracking-wide text-slate-muted">
            <th scope="col" className="px-6 py-3">
              Date
            </th>
            <th scope="col" className="px-4 py-3">
              Subject
            </th>
            <th scope="col" className="px-4 py-3">
              Topic
            </th>
            <th scope="col" className="px-4 py-3">
              Type
            </th>
            <th scope="col" className="px-4 py-3">
              Difficulty
            </th>
            <th scope="col" className="px-4 py-3">
              Quality
            </th>
            <th scope="col" className="px-4 py-3">
              Status
            </th>
            <th scope="col" className="px-6 py-3">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {isLoading &&
            skeletonRows.map((rowIndex) => (
              <tr key={rowIndex} className="border-b border-slate-50">
                <td className="px-6 py-3.5">
                  <Skeleton className="h-4 w-28" />
                </td>
                <td className="px-4 py-3.5">
                  <Skeleton className="h-4 w-20" />
                </td>
                <td className="px-4 py-3.5">
                  <Skeleton className="h-4 w-24" />
                </td>
                <td className="px-4 py-3.5">
                  <Skeleton className="h-4 w-10" />
                </td>
                <td className="px-4 py-3.5">
                  <Skeleton className="h-7 w-7 rounded-full" />
                </td>
                <td className="px-4 py-3.5">
                  <Skeleton className="h-4 w-8" />
                </td>
                <td className="px-4 py-3.5">
                  <Skeleton className="h-5 w-16 rounded-full" />
                </td>
                <td className="px-6 py-3.5">
                  <Skeleton className="h-8 w-8 rounded-lg" />
                </td>
              </tr>
            ))}
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
                {emptyMessage}
              </td>
            </tr>
          )}
          {!isLoading &&
            !isError &&
            rows.map((row) => {
              const isFrq = row.type.toLowerCase() === "frq";
              const isDeleting = deletingRunId === row.run_id;
              return (
                <tr
                  key={row.run_id}
                  className="border-b border-slate-50 transition-colors hover:bg-slate-50/80"
                >
                  <td className="px-6 py-3.5 text-slate-700">{formatDateTime(row.created_at)}</td>
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
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => onView?.(row)}
                        disabled={isFrq}
                        title={
                          isFrq
                            ? "FRQ practice is not available yet"
                            : "View question"
                        }
                        aria-label={isFrq ? "FRQ practice not available" : "View question"}
                        className={`rounded-lg p-1.5 transition-colors ${
                          isFrq
                            ? "cursor-not-allowed text-slate-300"
                            : "text-slate-muted hover:bg-slate-100 hover:text-brand"
                        }`}
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      {showDelete && (
                        <button
                          type="button"
                          onClick={() => onDelete?.(row)}
                          disabled={isDeleting}
                          title="Delete"
                          aria-label="Delete generation"
                          className="rounded-lg p-1.5 text-slate-muted transition-colors hover:bg-red-50 hover:text-error disabled:opacity-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>
    </div>
  );
}
