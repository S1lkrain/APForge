import { GraduationCap, LayoutDashboard } from "lucide-react";
import { useHashPath, useNavigate } from "../../lib/router";

export function Sidebar() {
  const path = useHashPath();
  const navigate = useNavigate();
  const onDashboard = path === "/";

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-2.5 border-b border-slate-100 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-white">
          <GraduationCap className="h-5 w-5" />
        </div>
        <span className="text-lg font-semibold text-slate-900">AP Practice</span>
      </div>

      <nav className="flex-1 px-3 py-4">
        <button
          type="button"
          onClick={() => navigate("/")}
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
            onDashboard
              ? "bg-brand-muted text-brand"
              : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          }`}
        >
          <LayoutDashboard className="h-4 w-4" />
          Dashboard
        </button>
      </nav>
    </aside>
  );
}
