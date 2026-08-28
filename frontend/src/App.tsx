import { useQuery } from "@tanstack/react-query";
import { Link, Route, Routes } from "react-router-dom";

import { api } from "@/lib/api";

interface HealthResponse {
  status: string;
  database: string;
}

function HealthBadge() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<HealthResponse>("/health")).data,
  });

  if (isLoading) return <span className="text-slate-400">checking API…</span>;
  if (isError || !data) return <span className="text-red-500">API unreachable</span>;
  return (
    <span className="text-emerald-600">
      API {data.status} · DB {data.database}
    </span>
  );
}

function Dashboard() {
  return (
    <div className="space-y-2">
      <h2 className="text-xl font-semibold">Dashboard</h2>
      <p className="text-slate-500">
        Modules land here as they are built. Next up: authentication, then the Job Tracker.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <Link to="/" className="text-lg font-bold">
            Life<span className="text-emerald-600">OS</span>
          </Link>
          <HealthBadge />
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-6 py-10">
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  );
}
