import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { listItems } from "../api/client";
import { PracticeSession } from "../components/practice/PracticeSession";
import { difficultyColor, formatSubject } from "../lib/format";
import { getSampleRunIds } from "../lib/samplePractice";
import { useNavigate } from "../lib/router";

interface SamplePracticePageProps {
  sampleId: string;
  index: number;
}

export function SamplePracticePage({ sampleId, index }: SamplePracticePageProps) {
  const navigate = useNavigate();
  const runIds = getSampleRunIds(sampleId);
  const runId = runIds[index];

  const { data, isLoading, isError } = useQuery({
    queryKey: ["items", "sample", sampleId, runId],
    queryFn: () => listItems({ run_id: runId, page_size: 1 }),
    enabled: Boolean(runId),
  });

  const item = data?.items[0];
  const total = runIds.length;
  const hasPrev = index > 0;
  const hasNext = index < total - 1;

  if (!runId) {
    return (
      <section className="rounded-xl border border-slate-100 bg-white p-8 text-center shadow-sm">
        <h1 className="text-lg font-semibold text-slate-900">Sample not found</h1>
        <p className="mt-2 text-sm text-slate-muted">
          Start a free sample from the dashboard to practice here.
        </p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>
      </section>
    );
  }

  if (isLoading) {
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
        <button
          type="button"
          onClick={() => navigate("/")}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white"
        >
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
        <span className="text-sm font-medium text-slate-600">
          Sample question {index + 1} of {total}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={!hasPrev}
            onClick={() => navigate(`/practice/sample/${sampleId}/${index - 1}`)}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm disabled:opacity-40"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>
          <button
            type="button"
            disabled={!hasNext}
            onClick={() => navigate(`/practice/sample/${sampleId}/${index + 1}`)}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-muted">
        <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 font-medium text-slate-700">
          {formatSubject(item.subject)}
        </span>
        <span
          className={`inline-flex h-7 w-7 items-center justify-center rounded-full border font-semibold ${difficultyColor(item.difficulty)}`}
        >
          {item.difficulty}
        </span>
      </div>

      <PracticeSession item={item} />
    </div>
  );
}
