import { GraduationCap, History, LayoutDashboard } from "lucide-react";
import { isGenerationHistoryPath, useHashPath, useNavigate } from "../../lib/router";

function navButtonClass(active: boolean): string {
  return `flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
    active
      ? "bg-brand-muted text-brand"
      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
  }`;
}

export function Sidebar() {
  const path = useHashPath();
  const navigate = useNavigate();
  const onDashboard = path === "/";
  const onHistory = isGenerationHistoryPath(path);

  return (
    <aside className="fixed left-0 top-0 z-10 flex h-screen w-60 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-2.5 border-b border-slate-100 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-white">
          <GraduationCap className="h-5 w-5" />
        </div>
        <span className="text-lg font-semibold text-slate-900">AP Practice</span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-4" aria-label="Main navigation">
        <button
          type="button"
          onClick={() => navigate("/")}
          className={navButtonClass(onDashboard)}
          aria-current={onDashboard ? "page" : undefined}
        >
          <LayoutDashboard className="h-4 w-4" />
          Dashboard
        </button>
        <button
          type="button"
          onClick={() => navigate("/generation-history")}
          className={navButtonClass(onHistory)}
          aria-current={onHistory ? "page" : undefined}
        >
          <History className="h-4 w-4" />
          Generation History
        </button>
      </nav>
    </aside>
  );
}
