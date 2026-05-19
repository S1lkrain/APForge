import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { GenerationHistoryPage } from "./pages/GenerationHistoryPage";
import { PracticePage } from "./pages/PracticePage";
import { isGenerationHistoryPath, matchPracticePath, useHashPath } from "./lib/router";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function AppRoutes() {
  const path = useHashPath();
  const practiceRunId = matchPracticePath(path);

  if (practiceRunId) {
    return <PracticePage runId={practiceRunId} />;
  }

  if (isGenerationHistoryPath(path)) {
    return <GenerationHistoryPage />;
  }

  return <Dashboard />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppShell>
        <AppRoutes />
      </AppShell>
    </QueryClientProvider>
  );
}
