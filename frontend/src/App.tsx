import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, Navigate, NavLink, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/features/auth/AuthContext";
import { fmtTime } from "@/features/calendar/dateUtils";
import { useOccurrences } from "@/features/calendar/queries";
import { currentMonth, formatCents } from "@/features/finance/money";
import { useSummary } from "@/features/finance/queries";
import { StatCards } from "@/features/jobTracker/StatCards";
import { useProjects } from "@/features/projects/queries";
import { api } from "@/lib/api";
import CalendarPage from "@/pages/CalendarPage";
import FinancePage from "@/pages/FinancePage";
import JobTrackerPage from "@/pages/JobTrackerPage";
import LoginPage from "@/pages/LoginPage";
import ProjectBoardPage from "@/pages/ProjectBoardPage";
import ProjectsPage from "@/pages/ProjectsPage";
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

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/job-tracker", label: "Job Tracker" },
  { to: "/projects", label: "Projects" },
  { to: "/calendar", label: "Calendar" },
  { to: "/finance", label: "Finance" },
];

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
              {NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    isActive
                      ? "font-medium text-emerald-600"
                      : "text-slate-500 hover:text-slate-800"
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

function ProjectsSummary() {
  const { data: projects = [] } = useProjects();
  const totalTasks = projects.reduce((sum, project) => sum + project.task_count, 0);
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-2xl font-bold tabular-nums">{projects.length}</div>
      <div className="text-xs text-slate-500">
        projects · {totalTasks} task{totalTasks === 1 ? "" : "s"}
      </div>
    </div>
  );
}

function UpcomingEvents() {
  const from = useMemoNow();
  const to = new Date(new Date(from).getTime() + 14 * 24 * 60 * 60 * 1000).toISOString();
  const { data: occurrences = [] } = useOccurrences(from, to);
  const next = occurrences.slice(0, 5);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      {next.length === 0 ? (
        <p className="text-sm text-slate-500">Nothing in the next two weeks.</p>
      ) : (
        <ul className="space-y-1.5 text-sm">
          {next.map((occurrence, index) => {
            const start = new Date(occurrence.start_at);
            return (
              <li key={`${occurrence.event_id}-${index}`} className="flex justify-between gap-4">
                <span className="truncate">{occurrence.title}</span>
                <span className="shrink-0 text-slate-400">
                  {start.toLocaleDateString([], { month: "short", day: "numeric" })}
                  {!occurrence.all_day && ` · ${fmtTime(start)}`}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/** A single "now" ISO string that stays stable for the component's lifetime. */
function useMemoNow(): string {
  return useMemo(() => new Date().toISOString(), []);
}

function FinanceSummaryCard() {
  const { data } = useSummary(currentMonth());
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-2xl font-bold tabular-nums">
        {data ? formatCents(data.net_cents) : "–"}
      </div>
      <div className="text-xs text-slate-500">
        net this month{data ? ` · ${Math.round(data.savings_rate * 100)}% saved` : ""}
      </div>
    </div>
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

      <div className="grid gap-6 md:grid-cols-3">
        <section>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-500">Projects</h3>
            <Link to="/projects" className="text-sm text-emerald-600 hover:underline">
              Open →
            </Link>
          </div>
          <ProjectsSummary />
        </section>

        <section>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-500">Finance</h3>
            <Link to="/finance" className="text-sm text-emerald-600 hover:underline">
              Open →
            </Link>
          </div>
          <FinanceSummaryCard />
        </section>

        <section>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-500">Upcoming</h3>
            <Link to="/calendar" className="text-sm text-emerald-600 hover:underline">
              Open →
            </Link>
          </div>
          <UpcomingEvents />
        </section>
      </div>
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
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId"
            element={
              <ProtectedRoute>
                <ProjectBoardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/calendar"
            element={
              <ProtectedRoute>
                <CalendarPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/finance"
            element={
              <ProtectedRoute>
                <FinancePage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
