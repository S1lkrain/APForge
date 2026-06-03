import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Layers,
  ListChecks,
  Loader2,
  Sparkles,
  Target,
} from "lucide-react";
import { useState } from "react";
import { generateSample, getPublicConfig } from "../../api/client";
import type { GenerateRequest, SampleGenerateResponse, Subject } from "../../api/types";
import { TOPIC_OPTIONS } from "../../lib/format";
import { saveSampleRunIds } from "../../lib/samplePractice";
import {
  isFreeSampleConsumedLocally,
  markFreeSampleConsumedLocally,
} from "../../lib/session";

interface FreeSampleCardProps {
  onSampleComplete?: (result: SampleGenerateResponse) => void;
  onPracticeNavigate?: (sampleId: string) => void;
}

export function FreeSampleCard({ onSampleComplete, onPracticeNavigate }: FreeSampleCardProps) {
  const queryClient = useQueryClient();
  const [subject] = useState<Subject>("ap_precalculus");
  const [skill, setSkill] = useState("rates-of-change");
  const [customSkill, setCustomSkill] = useState("");
  const [difficulty, setDifficulty] = useState(3);
  const [error, setError] = useState<string | null>(null);
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [lastSample, setLastSample] = useState<SampleGenerateResponse | null>(null);

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: getPublicConfig,
  });

  const sampleDisabled = !config?.free_sample_available || isFreeSampleConsumedLocally();

  const mutation = useMutation({
    mutationFn: (payload: GenerateRequest) => generateSample(payload),
    onSuccess: (data) => {
      setError(null);
      setLastSample(data);
      setSummaryOpen(true);
      if (data.claim_status === "consumed") {
        markFreeSampleConsumedLocally();
      }
      const runIds = data.items.map((item) => item.run_id);
      saveSampleRunIds(data.sample_id, runIds);
      void queryClient.invalidateQueries({ queryKey: ["config"] });
      void queryClient.invalidateQueries({ queryKey: ["items"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
      onSampleComplete?.(data);
      if (runIds.length > 0) {
        onPracticeNavigate?.(data.sample_id);
      }
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const resolvedSkill = skill === "custom" ? customSkill.trim() : skill;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!resolvedSkill) {
      setError("Please enter a topic.");
      return;
    }
    mutation.mutate({
      subject,
      skill: resolvedSkill,
      difficulty,
      type: "mcq",
    });
  }

  return (
    <section className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Free 5-question sample</h2>
      <p className="mt-1 text-sm text-slate-muted">
        Try APForge with a one-time sample pack powered by APForge Core. No API key required.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="block">
            <span className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700">
              <BookOpen className="h-4 w-4 text-brand" />
              Subject
            </span>
            <div className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700">
              AP Precalculus
            </div>
          </div>

          <label className="block">
            <span className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700">
              <Target className="h-4 w-4 text-brand" />
              Topic
            </span>
            <select
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm shadow-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
            >
              {TOPIC_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
              <option value="custom">Custom…</option>
            </select>
          </label>

          <div className="block">
            <span className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700">
              <ListChecks className="h-4 w-4 text-brand" />
              Question Type
            </span>
            <div className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700">
              Multiple Choice
            </div>
          </div>
        </div>

        {skill === "custom" && (
          <label className="block max-w-md">
            <span className="mb-1.5 text-sm font-medium text-slate-700">Custom topic</span>
            <input
              type="text"
              value={customSkill}
              onChange={(e) => setCustomSkill(e.target.value)}
              placeholder="e.g. rates-of-change"
              className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm shadow-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
            />
          </label>
        )}

        <label className="block max-w-xl">
          <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
            <Layers className="h-4 w-4 text-brand" />
            Difficulty: <span className="font-semibold text-brand">{difficulty}</span>
          </span>
          <input
            type="range"
            min={1}
            max={5}
            value={difficulty}
            onChange={(e) => setDifficulty(Number(e.target.value))}
            className="h-2 w-full cursor-pointer accent-brand"
          />
        </label>

        {error && (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-error">
            {error}
          </p>
        )}

        {!config?.core_configured && (
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            APForge Core is not configured on the server. Set APFORGE_CORE_API_KEY to enable the free
            sample.
          </p>
        )}

        {sampleDisabled && config?.free_sample_available === false && (
          <p className="text-sm text-slate-muted">
            Your free sample has been used for this browser session. Connect your own API key below
            to generate more questions.
          </p>
        )}

        <button
          type="submit"
          disabled={mutation.isPending || sampleDisabled || !config?.core_configured}
          className="mx-auto flex w-full max-w-md items-center justify-center gap-2 rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {mutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {mutation.isPending
            ? "Generating sample (this may take a minute)…"
            : "Generate free 5-question sample"}
        </button>
      </form>

      {lastSample && (
        <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50">
          <button
            type="button"
            onClick={() => setSummaryOpen((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-slate-800"
          >
            Validation summary ({lastSample.usable_count} usable of {lastSample.validation_report.total})
            {summaryOpen ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
          {summaryOpen && (
            <div className="border-t border-slate-200 px-4 py-3 text-sm text-slate-700">
              <p>Claim status: {lastSample.claim_status}</p>
              <p className="mt-1">
                Status counts:{" "}
                {Object.entries(lastSample.validation_report.status_counts)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(", ") || "none"}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
