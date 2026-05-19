import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2 } from "lucide-react";
import { listItems } from "../api/client";
import { PracticeSession } from "../components/practice/PracticeSession";
import { difficultyColor, formatSubject } from "../lib/format";
import { useNavigate } from "../lib/router";

interface PracticePageProps {
  runId: string;
}

export function PracticePage({ runId }: PracticePageProps) {
  const navigate = useNavigate();
  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ["items"],
    queryFn: () => listItems(),
  });

  const item = data?.items.find((row) => row.run_id === runId);
  const waitingForItem = !item && (isLoading || isFetching);

  if (waitingForItem) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-muted">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Loading question…
      </div>
    );
  }

  if (isError || !item) {
    return (
      <section className="rounded-xl border border-slate-100 bg-white p-8 text-center shadow-sm">
        <h1 className="text-lg font-semibold text-slate-900">Question not found</h1>
        <p className="mt-2 text-sm text-slate-muted">
          This item may have been removed or the link is invalid.
        </p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>
      </section>
    );
  }

  if (item.type.toLowerCase() === "frq") {
    return (
      <section className="rounded-xl border border-slate-100 bg-white p-8 text-center shadow-sm">
        <h1 className="text-lg font-semibold text-slate-900">
          Free response practice is not available yet
        </h1>
        <p className="mt-2 text-sm text-slate-muted">
          MCQ practice is available from your recent generations.
        </p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-muted hover:text-brand"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-muted">
          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 font-medium text-slate-700">
            {formatSubject(item.subject)}
          </span>
          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 capitalize">
            {item.skill.replace(/-/g, " ")}
          </span>
          <span
            className={`inline-flex h-7 w-7 items-center justify-center rounded-full border font-semibold ${difficultyColor(item.difficulty)}`}
          >
            {item.difficulty}
          </span>
          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 uppercase">
            {item.type}
          </span>
        </div>
      </div>

      <PracticeSession item={item} />
    </div>
  );
}
