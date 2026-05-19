import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo } from "react";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

function buildPageNumbers(current: number, totalPages: number): (number | "ellipsis")[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const pages: (number | "ellipsis")[] = [1];

  if (current > 3) {
    pages.push("ellipsis");
  }

  const start = Math.max(2, current - 1);
  const end = Math.min(totalPages - 1, current + 1);

  for (let p = start; p <= end; p += 1) {
    pages.push(p);
  }

  if (current < totalPages - 2) {
    pages.push("ellipsis");
  }

  pages.push(totalPages);
  return pages;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
  const safePage = totalPages === 0 ? 1 : Math.min(page, totalPages);
  const start = total === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const end = Math.min(safePage * pageSize, total);

  const pageNumbers = useMemo(
    () => buildPageNumbers(safePage, Math.max(1, totalPages)),
    [safePage, totalPages],
  );

  if (total === 0) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 px-6 py-4 text-sm text-slate-muted">
        <span>No results</span>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 px-6 py-4">
      <p className="text-sm text-slate-muted" aria-live="polite">
        Showing <span className="font-medium text-slate-700">{start}</span> to{" "}
        <span className="font-medium text-slate-700">{end}</span> of{" "}
        <span className="font-medium text-slate-700">{total}</span> results
      </p>

      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onPageChange(safePage - 1)}
          disabled={safePage <= 1}
          aria-label="Previous page"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        {pageNumbers.map((item, index) =>
          item === "ellipsis" ? (
            <span
              key={`ellipsis-${index}`}
              className="flex h-8 w-8 items-center justify-center text-slate-400"
            >
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              onClick={() => onPageChange(item)}
              aria-label={`Page ${item}`}
              aria-current={item === safePage ? "page" : undefined}
              className={`flex h-8 min-w-8 items-center justify-center rounded-lg px-2 text-sm font-medium transition-colors ${
                item === safePage
                  ? "bg-brand text-white shadow-sm"
                  : "border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {item}
            </button>
          ),
        )}

        <button
          type="button"
          onClick={() => onPageChange(safePage + 1)}
          disabled={totalPages === 0 || safePage >= totalPages}
          aria-label="Next page"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
