const SAMPLE_RUNS_PREFIX = "ap_sample_runs_";

export function saveSampleRunIds(sampleId: string, runIds: string[]): void {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(`${SAMPLE_RUNS_PREFIX}${sampleId}`, JSON.stringify(runIds));
}

export function getSampleRunIds(sampleId: string): string[] {
  if (typeof window === "undefined") {
    return [];
  }
  const raw = sessionStorage.getItem(`${SAMPLE_RUNS_PREFIX}${sampleId}`);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === "string") : [];
  } catch {
    return [];
  }
}
