import { useQuery } from "@tanstack/react-query";
import { Link, Navigate, NavLink, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { StatCards } from "@/features/jobTracker/StatCards";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api";
import JobTrackerPage from "@/pages/JobTrackerPage";
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
  const authed = status === "authenticated";

  return (
    <header className="border-b border-slate-200 dark:border-slate-800">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-6 py-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-lg font-bold">
            Life<span className="text-emerald-600">OS</span>
          </Link>
          {authed && (
            <nav className="flex gap-4 text-sm">
              {[
                { to: "/", label: "Dashboard" },
                { to: "/job-tracker", label: "Job Tracker" },
              ].map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    isActive ? "font-medium text-emerald-600" : "text-slate-500 hover:text-slate-800"
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          )}
        </div>
        <div className="flex items-center gap-4 text-sm">
          <HealthBadge />
          {authed && user && (
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
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Dashboard</h2>
        <p className="text-slate-500">
          Signed in as{" "}
          <span className="font-medium text-slate-700 dark:text-slate-200">{user?.email}</span>.
        </p>
      </div>
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-medium text-slate-500">Job search</h3>
          <Link to="/job-tracker" className="text-sm text-emerald-600 hover:underline">
            Open Job Tracker →
          </Link>
        </div>
        <StatCards />
      </section>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
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
          <Route
            path="/job-tracker"
            element={
              <ProtectedRoute>
                <JobTrackerPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
