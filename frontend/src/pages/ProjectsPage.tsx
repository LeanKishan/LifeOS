import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { useCreateProject, useProjects } from "@/features/projects/queries";

export default function ProjectsPage() {
  const { data: projects = [], isLoading } = useProjects();
  const create = useCreateProject();
  const [name, setName] = useState("");

  function submit(event: FormEvent): void {
    event.preventDefault();
    const value = name.trim();
    if (value) create.mutate({ name: value }, { onSuccess: () => setName("") });
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Projects</h2>
        <form onSubmit={submit} className="flex gap-2">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="New project name"
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
          />
          <button
            type="submit"
            disabled={create.isPending}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Create
          </button>
        </form>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {!isLoading && projects.length === 0 && (
        <p className="text-sm text-slate-500">No projects yet — create your first one.</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Link
            key={project.id}
            to={`/projects/${project.id}`}
            className="rounded-lg border border-slate-200 bg-white p-4 hover:border-emerald-400 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="font-medium">{project.name}</div>
            {project.description && (
              <p className="mt-1 line-clamp-2 text-sm text-slate-500">{project.description}</p>
            )}
            <div className="mt-3 text-xs text-slate-400">{project.task_count} tasks</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
