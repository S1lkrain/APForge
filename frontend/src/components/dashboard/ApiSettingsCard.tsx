import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ChevronDown, ChevronUp, KeyRound, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { getPublicConfig } from "../../api/client";
import {
  clearStoredApiKeys,
  getStoredApiKey,
  getStoredLlmApiKey,
  hasStoredApiKeys,
  saveApiKeys,
} from "../../lib/settingsStorage";

export function ApiSettingsCard() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(!hasStoredApiKeys());
  const [apiKey, setApiKey] = useState("");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [saved, setSaved] = useState(false);

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: getPublicConfig,
  });

  useEffect(() => {
    setApiKey(getStoredApiKey());
    setLlmApiKey(getStoredLlmApiKey());
  }, []);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    saveApiKeys(apiKey, llmApiKey);
    setSaved(true);
    void queryClient.invalidateQueries();
    window.setTimeout(() => setSaved(false), 2500);
  }

  function handleClear() {
    clearStoredApiKeys();
    setApiKey("");
    setLlmApiKey("");
    void queryClient.invalidateQueries();
  }

  const stored = hasStoredApiKeys();

  return (
    <section className="rounded-xl border border-slate-100 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-6 py-4 text-left"
      >
        <div className="flex flex-wrap items-center gap-2">
          <KeyRound className="h-4 w-4 text-brand" />
          <span className="text-lg font-semibold text-slate-900">API Keys</span>
          {stored && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
              Saved in browser
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
        <div className="border-t border-slate-100 px-6 pb-6 pt-2">
          <p className="text-sm text-slate-muted">
            Keys are stored only in this browser (localStorage). They are sent on API requests and
            never written to the server disk.
          </p>

          {config && (
            <ul className="mt-3 space-y-1 text-xs text-slate-600">
              <li className="flex items-center gap-2">
                <Shield className="h-3.5 w-3.5" />
                Backend access key required:{" "}
                <span className="font-medium">{config.api_auth_required ? "Yes" : "No"}</span>
              </li>
              <li className="flex items-center gap-2">
                <Shield className="h-3.5 w-3.5" />
                Server default LLM key configured:{" "}
                <span className="font-medium">{config.llm_configured ? "Yes" : "No"}</span>
              </li>
            </ul>
          )}

          <form onSubmit={handleSave} className="mt-5 space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                Access API Key
              </span>
              <span className="mb-1.5 block text-xs text-slate-muted">
                Matches backend <code className="rounded bg-slate-100 px-1">API_KEY</code> — sent as{" "}
                <code className="rounded bg-slate-100 px-1">X-API-Key</code>
              </span>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={config?.api_auth_required ? "Required for API calls" : "Optional"}
                autoComplete="off"
                className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm shadow-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                LLM API Key (OpenAI-compatible)
              </span>
              <span className="mb-1.5 block text-xs text-slate-muted">
                Overrides server <code className="rounded bg-slate-100 px-1">OPENAI_API_KEY</code>{" "}
                for generation only — sent as{" "}
                <code className="rounded bg-slate-100 px-1">X-LLM-API-Key</code>
              </span>
              <input
                type="password"
                value={llmApiKey}
                onChange={(e) => setLlmApiKey(e.target.value)}
                placeholder={
                  config?.llm_configured
                    ? "Optional — server key is configured"
                    : "Required for real LLM generation"
                }
                autoComplete="off"
                className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm shadow-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
              />
            </label>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <button
                type="submit"
                className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-600"
              >
                Save keys
              </button>
              <button
                type="button"
                onClick={handleClear}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              >
                Clear
              </button>
              {saved && (
                <span className="flex items-center gap-1 text-sm text-emerald-600">
                  <CheckCircle2 className="h-4 w-4" />
                  Saved
                </span>
              )}
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
