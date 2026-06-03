const SESSION_STORAGE_KEY = "apforge_session_id";
const FREE_SAMPLE_CONSUMED_KEY = "ap_free_sample_consumed";

export function getOrCreateSessionId(): string {
  if (typeof window === "undefined") {
    return "";
  }
  const existing = localStorage.getItem(SESSION_STORAGE_KEY)?.trim();
  if (existing) {
    return existing;
  }
  const created = crypto.randomUUID();
  localStorage.setItem(SESSION_STORAGE_KEY, created);
  return created;
}

export function isFreeSampleConsumedLocally(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return localStorage.getItem(FREE_SAMPLE_CONSUMED_KEY) === "1";
}

export function markFreeSampleConsumedLocally(): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(FREE_SAMPLE_CONSUMED_KEY, "1");
}

export function clearFreeSampleConsumedLocally(): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.removeItem(FREE_SAMPLE_CONSUMED_KEY);
}
