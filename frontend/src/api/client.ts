import type { DashboardStats, GenerateRequest, GenerateResponse, ItemRow } from "./types";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
const apiKey = import.meta.env.VITE_API_KEY ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // ignore parse errors
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export function generate(payload: GenerateRequest): Promise<GenerateResponse> {
  return request<GenerateResponse>("/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listItems(params?: {
  subject?: string;
  skill?: string;
  difficulty?: number;
}): Promise<{ items: ItemRow[] }> {
  const search = new URLSearchParams();
  if (params?.subject) search.set("subject", params.subject);
  if (params?.skill) search.set("skill", params.skill);
  if (params?.difficulty !== undefined) search.set("difficulty", String(params.difficulty));
  const query = search.toString();
  return request<{ items: ItemRow[] }>(`/items${query ? `?${query}` : ""}`);
}

export function getStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/stats");
}
