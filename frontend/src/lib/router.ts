import { useCallback, useEffect, useState } from "react";

export function getHashPath(): string {
  let hash = window.location.hash.replace(/^#/, "") || "/";
  hash = hash.startsWith("/") ? hash : `/${hash}`;
  if (hash.length > 1 && hash.endsWith("/")) {
    hash = hash.slice(0, -1);
  }
  return hash;
}

export function useHashPath(): string {
  const [path, setPath] = useState(getHashPath);

  useEffect(() => {
    const onHashChange = () => setPath(getHashPath());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return path;
}

export function useNavigate() {
  return useCallback((to: string) => {
    const normalized = to.startsWith("/") ? to : `/${to}`;
    window.location.hash = normalized;
  }, []);
}

export function matchPracticePath(path: string): string | null {
  const single = path.match(/^\/practice\/([^/]+)$/);
  if (single && !single[1].startsWith("sample")) {
    return single[1];
  }
  return null;
}

export function matchSamplePracticePath(path: string): { sampleId: string; index: number } | null {
  const match = path.match(/^\/practice\/sample\/([^/]+)\/(\d+)$/);
  if (!match) {
    return null;
  }
  return { sampleId: match[1], index: Number(match[2]) };
}

export function isGenerationHistoryPath(path: string): boolean {
  return path === "/generation-history";
}
