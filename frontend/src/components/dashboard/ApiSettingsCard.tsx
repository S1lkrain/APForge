import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, ChevronDown, ChevronUp, KeyRound, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { getPublicConfig } from "../../api/client";
import {
  clearStoredApiKeys,
  getStoredApiKey,
  hasStoredApiKeys,
  saveApiKeys,
} from "../../lib/settingsStorage";

export function ApiSettingsCard() {
  const [open, setOpen] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: getPublicConfig,
  });

  useEffect(() => {
    setApiKey(getStoredApiKey());
  }, []);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    saveApiKeys(apiKey, "");
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  }

  function handleClear() {
    clearStoredApiKeys();
    setApiKey("");
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
          <Shield className="h-4 w-4 text-slate-500" />
          <span className="text-base font-medium text-slate-800">Backend access key</span>
          {stored && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
              Saved
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
            Optional <code className="rounded bg-slate-100 px-1">API_KEY</code> for protected
            deployments. LLM keys are configured in &quot;Use my own API key&quot; above — not stored
            in this browser.
          </p>

          {config && (
            <ul className="mt-3 space-y-1 text-xs text-slate-600">
              <li>
                Backend access key required:{" "}
                <span className="font-medium">{config.api_auth_required ? "Yes" : "No"}</span>
              </li>
              <li>
                APForge Core configured:{" "}
                <span className="font-medium">{config.core_configured ? "Yes" : "No"}</span>
              </li>
            </ul>
          )}

          <form onSubmit={handleSave} className="mt-5 space-y-4">
            <label className="block max-w-md">
              <span className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700">
                <KeyRound className="h-4 w-4 text-brand" />
                Access API Key
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

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="submit"
                className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600"
              >
                Save
              </button>
              <button
                type="button"
                onClick={handleClear}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
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
