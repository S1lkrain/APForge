import type {
  DashboardStats,
  GenerateRequest,
  GenerateResponse,
  ItemsListResponse,
  ListItemsParams,
  PublicConfig,
  SampleGenerateResponse,
} from "./types";
import { getEffectiveApiKey } from "../lib/settingsStorage";
import { getOrCreateSessionId } from "../lib/session";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

function buildAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "X-APForge-Session": getOrCreateSessionId(),
  };
  const apiKey = getEffectiveApiKey();
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
    ...buildAuthHeaders(),
  };

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

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function getPublicConfig(): Promise<PublicConfig> {
  return request<PublicConfig>("/config");
}

export function generate(payload: GenerateRequest): Promise<GenerateResponse> {
  return request<GenerateResponse>("/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function generateSample(payload: GenerateRequest): Promise<SampleGenerateResponse> {
  return request<SampleGenerateResponse>("/generate/sample", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function connectByokCredentials(apiKey: string, model?: string): Promise<void> {
  return request<void>("/byok/credentials", {
    method: "POST",
    body: JSON.stringify({ api_key: apiKey, model: model || undefined }),
  });
}

export function disconnectByokCredentials(): Promise<void> {
  return request<void>("/byok/credentials", { method: "DELETE" });
}

export function listItems(params?: ListItemsParams): Promise<ItemsListResponse> {
  const search = new URLSearchParams();
  if (params?.run_id) search.set("run_id", params.run_id);
  if (params?.sample_id) search.set("sample_id", params.sample_id);
  if (params?.subject) search.set("subject", params.subject);
  if (params?.skill) search.set("skill", params.skill);
  if (params?.difficulty !== undefined) search.set("difficulty", String(params.difficulty));
  if (params?.type) search.set("type", params.type);
  if (params?.status) search.set("status", params.status);
  if (params?.q) search.set("q", params.q);
  if (params?.quality_min !== undefined) search.set("quality_min", String(params.quality_min));
  if (params?.quality_max !== undefined) search.set("quality_max", String(params.quality_max));
  if (params?.has_quality !== undefined) search.set("has_quality", String(params.has_quality));
  if (params?.sort) search.set("sort", params.sort);
  if (params?.page !== undefined) search.set("page", String(params.page));
  if (params?.page_size !== undefined) search.set("page_size", String(params.page_size));
  const query = search.toString();
  return request<ItemsListResponse>(`/items${query ? `?${query}` : ""}`);
}

export function deleteItem(runId: string): Promise<void> {
  return request<void>(`/items/${runId}`, { method: "DELETE" });
}

export function getStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/stats");
}
