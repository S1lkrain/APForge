import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { GenerationHistoryPage } from "./pages/GenerationHistoryPage";
import { PracticePage } from "./pages/PracticePage";
import {
  isGenerationHistoryPath,
  matchPracticePath,
  matchSamplePracticePath,
  useHashPath,
} from "./lib/router";
import { SamplePracticePage } from "./pages/SamplePracticePage";

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
  const samplePractice = matchSamplePracticePath(path);
  const practiceRunId = matchPracticePath(path);

  if (samplePractice) {
    return (
      <SamplePracticePage
        sampleId={samplePractice.sampleId}
        index={samplePractice.index}
      />
    );
  }

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
