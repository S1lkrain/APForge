import { useState } from "react";
import { useNavigate } from "../lib/router";
import { ApiSettingsCard } from "../components/dashboard/ApiSettingsCard";
import { GenerateCard } from "../components/dashboard/GenerateCard";
import { RecentTable } from "../components/dashboard/RecentTable";
import { StatCards } from "../components/dashboard/StatCards";
import { TopBar } from "../components/layout/TopBar";

export function Dashboard() {
  const navigate = useNavigate();
  const [lastResult, setLastResult] = useState<{ run_id: string; status: string } | null>(
    null,
  );

  return (
    <>
      <TopBar />
      <ApiSettingsCard />
      <GenerateCard
        onGenerated={setLastResult}
        onPracticeNavigate={(runId) => navigate(`/practice/${runId}`)}
      />
      {lastResult && (
        <p className="animate-banner-enter rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">
          Generated run <span className="font-mono text-xs">{lastResult.run_id}</span> — status:{" "}
          <span className="font-medium">{lastResult.status}</span>
        </p>
      )}
      <StatCards />
      <RecentTable />
    </>
  );
}
