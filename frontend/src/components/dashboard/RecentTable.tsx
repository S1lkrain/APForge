import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { listItems } from "../../api/client";
import type { ItemRow } from "../../api/types";
import { GenerationsTable } from "../history/GenerationsTable";
import { useNavigate } from "../../lib/router";

export function RecentTable() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["items", "recent"],
    queryFn: () => listItems({ page: 1, page_size: 5, sort: "newest" }),
  });

  const rows = data?.items ?? [];

  function openPractice(row: ItemRow) {
    if (row.type.toLowerCase() === "frq") return;
    navigate(`/practice/${row.run_id}`);
  }

  return (
    <section className="rounded-xl border border-slate-100 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-4">
        <h2 className="text-lg font-semibold text-slate-900">Recent Generations</h2>
        <button
          type="button"
          onClick={() => navigate("/generation-history")}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-brand transition-colors hover:text-blue-600"
        >
          View All History
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      <GenerationsTable
        rows={rows}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="No generations yet. Create your first question above."
        onView={openPractice}
      />
    </section>
  );
}
