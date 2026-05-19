import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="h-screen overflow-hidden bg-surface">
      <Sidebar />
      <main className="ml-60 h-screen overflow-y-auto">
        <div className="mx-auto max-w-6xl space-y-6 p-6 md:p-8">{children}</div>
      </main>
    </div>
  );
}
