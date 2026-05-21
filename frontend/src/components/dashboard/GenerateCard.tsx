import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  Layers,
  ListChecks,
  Loader2,
  Sparkles,
  Target,
} from "lucide-react";
import { useState } from "react";
import { generate } from "../../api/client";
import type { GenerateRequest, Subject } from "../../api/types";
import { TOPIC_OPTIONS } from "../../lib/format";
import { buildItemRowFromGenerate, upsertItemInCache } from "../../lib/itemsCache";

interface GenerateCardProps {
  onGenerated?: (result: { run_id: string; status: string }) => void;
  onPracticeNavigate?: (runId: string) => void;
}

export function GenerateCard({ onGenerated, onPracticeNavigate }: GenerateCardProps) {
  const queryClient = useQueryClient();
  const [subject] = useState<Subject>("ap_precalculus");
  const [skill, setSkill] = useState("rates-of-change");
  const [customSkill, setCustomSkill] = useState("");
  const [difficulty, setDifficulty] = useState(3);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: GenerateRequest) => generate(payload),
    onSuccess: (data, variables) => {
      setError(null);
      upsertItemInCache(queryClient, buildItemRowFromGenerate(data, variables));
      void queryClient.invalidateQueries({ queryKey: ["items"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
      onGenerated?.({ run_id: data.run_id, status: data.harness.status });
      onPracticeNavigate?.(data.run_id);
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
      <h2 className="text-lg font-semibold text-slate-900">Generate New Question</h2>
      <p className="mt-1 text-sm text-slate-muted">
        Choose parameters and generate a practice item.
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
            <p className="mt-1 text-xs text-slate-muted">Free response is coming soon.</p>
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
          <div className="mt-1 flex justify-between text-xs text-slate-muted">
            <span>1</span>
            <span>5</span>
          </div>
        </label>

        {error && (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-error">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={mutation.isPending}
          className="mx-auto flex w-full max-w-md items-center justify-center gap-2 rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white shadow-md transition-[transform,colors] duration-150 hover:bg-blue-600 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
        >
          {mutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {mutation.isPending ? "Generating…" : "Generate Question"}
        </button>
      </form>
    </section>
  );
}
