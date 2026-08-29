import { useMemo } from "react";
import { Link } from "react-router-dom";

import { Icon } from "@/components/icons";
import { Card, CardHeader, PageHeader, StatTile } from "@/components/ui";
import { useAuth } from "@/features/auth/AuthContext";
import { fmtTime } from "@/features/calendar/dateUtils";
import { useOccurrences } from "@/features/calendar/queries";
import { currentMonth, formatCents } from "@/features/finance/money";
import { useSummary } from "@/features/finance/queries";
import { useJobStats } from "@/features/jobTracker/queries";
import { useCourses, useReviewCount } from "@/features/learning/queries";
import { useProjects } from "@/features/projects/queries";

function OpenLink({ to }: { to: string }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-1 text-xs font-semibold text-brand-hi transition hover:gap-1.5"
    >
      Open <Icon name="arrowRight" size={13} />
    </Link>
  );
}

function JobStats() {
  const { data } = useJobStats();
  const pct = (n: number | undefined) => (n == null ? "–" : `${Math.round(n * 100)}%`);
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatTile label="Applications" value={data?.total ?? "–"} icon="briefcase" />
      <StatTile label="Active" value={data?.active ?? "–"} icon="clock" tone="violet" />
      <StatTile label="Response rate" value={pct(data?.response_rate)} icon="chart" tone="amber" />
      <StatTile label="Offers" value={data?.offers ?? "–"} icon="target" />
    </div>
  );
}

function ProjectsWidget() {
  const { data: projects = [] } = useProjects();
  const tasks = projects.reduce((s, p) => s + p.task_count, 0);
  return (
    <Card hover>
      <CardHeader title="Projects" action={<OpenLink to="/projects" />} />
      <div className="text-3xl font-bold tabular-nums text-content">{projects.length}</div>
      <p className="mt-0.5 text-sm text-muted">
        {tasks} task{tasks === 1 ? "" : "s"} across boards
      </p>
    </Card>
  );
}

function FinanceWidget() {
  const { data } = useSummary(currentMonth());
  return (
    <Card hover>
      <CardHeader title="Finance" action={<OpenLink to="/finance" />} />
      <div className="text-3xl font-bold tabular-nums text-content">
        {data ? formatCents(data.net_cents) : "–"}
      </div>
      <p className="mt-0.5 text-sm text-muted">
        net this month{data ? ` · ${Math.round(data.savings_rate * 100)}% saved` : ""}
      </p>
    </Card>
  );
}

function LearningWidget() {
  const { data: courses = [] } = useCourses();
  const { data: due = [] } = useReviewCount();
  return (
    <Card hover>
      <CardHeader title="Learning" action={<OpenLink to="/learning" />} />
      <div className="text-3xl font-bold tabular-nums text-content">{due.length}</div>
      <p className="mt-0.5 text-sm text-muted">
        cards due · {courses.length} course{courses.length === 1 ? "" : "s"}
      </p>
    </Card>
  );
}

function UpcomingWidget() {
  const from = useMemo(() => new Date().toISOString(), []);
  const to = useMemo(
    () => new Date(Date.now() + 14 * 864e5).toISOString(),
    [],
  );
  const { data: occ = [] } = useOccurrences(from, to);
  const next = occ.slice(0, 5);
  return (
    <Card hover>
      <CardHeader title="Upcoming" action={<OpenLink to="/calendar" />} />
      {next.length === 0 ? (
        <p className="text-sm text-muted">Nothing in the next two weeks.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {next.map((o, i) => {
            const start = new Date(o.start_at);
            return (
              <li key={`${o.event_id}-${i}`} className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2 truncate">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand-hi" />
                  <span className="truncate text-content">{o.title}</span>
                </span>
                <span className="shrink-0 tabular-nums text-faint">
                  {start.toLocaleDateString([], { month: "short", day: "numeric" })}
                  {!o.all_day && ` · ${fmtTime(start)}`}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const name = user?.full_name?.split(" ")[0] || user?.email?.split("@")[0] || "there";

  return (
    <div>
      <PageHeader
        title={
          <>
            {greet}, <span className="text-gradient">{name}</span>
          </>
        }
        subtitle="Here's everything at a glance."
      />

      <section className="mb-8 animate-fade-in-up stagger-1">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="label-eyebrow">Job search</h2>
          <OpenLink to="/job-tracker" />
        </div>
        <JobStats />
      </section>

      <section className="grid gap-4 animate-fade-in-up stagger-2 md:grid-cols-2 xl:grid-cols-4">
        <ProjectsWidget />
        <FinanceWidget />
        <LearningWidget />
        <UpcomingWidget />
      </section>
    </div>
  );
}
