const API_KEY_STORAGE = "ap_practice_api_key";
const LLM_KEY_STORAGE = "ap_practice_llm_api_key";

export function getStoredApiKey(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return localStorage.getItem(API_KEY_STORAGE)?.trim() ?? "";
}

export function getStoredLlmApiKey(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return localStorage.getItem(LLM_KEY_STORAGE)?.trim() ?? "";
}

export function getEffectiveApiKey(): string {
  return getStoredApiKey() || (import.meta.env.VITE_API_KEY ?? "").trim();
}

export function getEffectiveLlmApiKey(): string {
  return getStoredLlmApiKey();
}

export function saveApiKeys(apiKey: string, llmApiKey: string): void {
  const trimmedApi = apiKey.trim();
  const trimmedLlm = llmApiKey.trim();
  if (trimmedApi) {
    localStorage.setItem(API_KEY_STORAGE, trimmedApi);
  } else {
    localStorage.removeItem(API_KEY_STORAGE);
  }
  if (trimmedLlm) {
    localStorage.setItem(LLM_KEY_STORAGE, trimmedLlm);
  } else {
    localStorage.removeItem(LLM_KEY_STORAGE);
  }
  window.dispatchEvent(new CustomEvent("ap-settings-changed"));
}

export function clearStoredApiKeys(): void {
  localStorage.removeItem(API_KEY_STORAGE);
  localStorage.removeItem(LLM_KEY_STORAGE);
  window.dispatchEvent(new CustomEvent("ap-settings-changed"));
}

export function hasStoredApiKeys(): boolean {
  return Boolean(getStoredApiKey() || getStoredLlmApiKey());
}
