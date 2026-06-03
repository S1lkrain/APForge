import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ChevronDown, ChevronUp, KeyRound } from "lucide-react";
import { useState } from "react";
import {
  connectByokCredentials,
  disconnectByokCredentials,
  getPublicConfig,
} from "../../api/client";
import { GenerateCard } from "./GenerateCard";

interface ByokSectionProps {
  onGenerated?: (result: { run_id: string; status: string }) => void;
  onPracticeNavigate?: (runId: string) => void;
}

export function ByokSection({ onGenerated, onPracticeNavigate }: ByokSectionProps) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: getPublicConfig,
  });

  const connectMutation = useMutation({
    mutationFn: (key: string) => connectByokCredentials(key),
    onSuccess: () => {
      setApiKey("");
      setError(null);
      setSaved(true);
      void queryClient.invalidateQueries({ queryKey: ["config"] });
      window.setTimeout(() => setSaved(false), 2500);
    },
    onError: (err: Error) => setError(err.message),
  });

  const disconnectMutation = useMutation({
    mutationFn: () => disconnectByokCredentials(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["config"] });
    },
  });

  function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    if (!apiKey.trim()) {
      setError("Enter your OpenAI-compatible API key.");
      return;
    }
    connectMutation.mutate(apiKey.trim());
  }

  return (
    <section className="rounded-xl border border-slate-100 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-6 py-4 text-left"
      >
        <div className="flex flex-wrap items-center gap-2">
          <KeyRound className="h-4 w-4 text-slate-500" />
          <span className="text-base font-medium text-slate-800">Use my own API key</span>
          {config?.byok_connected && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
              Connected
            </span>
          )}
        </div>
        {open ? (
          <ChevronUp className="h-5 w-5 text-slate-muted" />
        ) : (
          <ChevronDown className="h-5 w-5 text-slate-muted" />
        )}
      </button>

      {open && (
        <div className="space-y-6 border-t border-slate-100 px-6 pb-6 pt-4">
          <p className="text-sm text-slate-muted">
            Your key is held in server memory for this browser session (about 24 hours). On
            serverless hosting you may need to reconnect after idle or deploy. Only standard OpenAI
            endpoints are supported in this preview.
          </p>

          <form onSubmit={handleConnect} className="max-w-md space-y-3">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                OpenAI-compatible API key
              </span>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                autoComplete="off"
                placeholder="sk-…"
                className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm shadow-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>
            {error && <p className="text-sm text-error">{error}</p>}
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="submit"
                disabled={connectMutation.isPending}
                className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-900 disabled:opacity-60"
              >
                Connect key
              </button>
              {config?.byok_connected && (
                <button
                  type="button"
                  onClick={() => disconnectMutation.mutate()}
                  className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Disconnect
                </button>
              )}
              {saved && (
                <span className="flex items-center gap-1 text-sm text-emerald-600">
                  <CheckCircle2 className="h-4 w-4" />
                  Connected
                </span>
              )}
            </div>
          </form>

          {config?.byok_connected && (
            <GenerateCard onGenerated={onGenerated} onPracticeNavigate={onPracticeNavigate} />
          )}
        </div>
      )}
    </section>
  );
}
