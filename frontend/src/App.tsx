import { useQuery } from "@tanstack/react-query";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";

interface HealthResponse {
  status: string;
  database: string;
}

function HealthBadge() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<HealthResponse>("/health")).data,
  });

  if (isLoading) return <span className="text-slate-400">checking…</span>;
  if (isError || !data) return <span className="text-red-500">API down</span>;
  return (
    <span className="text-emerald-600">
      API {data.status} · DB {data.database}
    </span>
  );
}

function Header() {
  const { status, user, logout } = useAuth();
  return (
    <header className="border-b border-slate-200 dark:border-slate-800">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
        <Link to="/" className="text-lg font-bold">
          Life<span className="text-emerald-600">OS</span>
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <HealthBadge />
          {status === "authenticated" && user && (
            <>
              <span className="text-slate-500">{user.email}</span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-slate-300 px-2 py-1 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
              >
                Log out
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function Dashboard() {
  const { user } = useAuth();
  return (
    <div className="space-y-2">
      <h2 className="text-xl font-semibold">Dashboard</h2>
      <p className="text-slate-500">
        Signed in as{" "}
        <span className="font-medium text-slate-700 dark:text-slate-200">{user?.email}</span>. Modules
        land here as they are built — next up: the Job Tracker.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <Header />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
