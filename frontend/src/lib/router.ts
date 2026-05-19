import { useCallback, useEffect, useState } from "react";

export function getHashPath(): string {
  const hash = window.location.hash.replace(/^#/, "") || "/";
  return hash.startsWith("/") ? hash : `/${hash}`;
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
  const match = path.match(/^\/practice\/([^/]+)$/);
  return match ? match[1] : null;
}
