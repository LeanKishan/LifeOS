import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Icon } from "@/components/icons";
import { Button, EmptyState, Input, LoadingRow, PageHeader } from "@/components/ui";
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
      <PageHeader
        title="Projects"
        subtitle="Kanban boards for everything you're shipping."
        actions={
          <form onSubmit={submit} className="flex gap-2">
            <Input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="New project name"
              className="w-44 sm:w-52"
            />
            <Button type="submit" variant="primary" icon="plus" loading={create.isPending}>
              Create
            </Button>
          </form>
        }
      />

      {isLoading && <LoadingRow />}
      {!isLoading && projects.length === 0 && (
        <EmptyState
          icon="kanban"
          title="No projects yet"
          description="Create your first board to start moving tasks."
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project, i) => (
          <Link
            key={project.id}
            to={`/projects/${project.id}`}
            className={`surface-card card-hover group animate-fade-in-up stagger-${Math.min(i + 1, 6)} p-5`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="font-semibold text-content">{project.name}</div>
              <Icon
                name="arrowRight"
                size={16}
                className="text-faint transition group-hover:translate-x-0.5 group-hover:text-brand-hi"
              />
            </div>
            {project.description && (
              <p className="mt-1.5 line-clamp-2 text-sm text-muted">{project.description}</p>
            )}
            <div className="mt-4 flex items-center gap-1.5 text-xs text-faint">
              <Icon name="layers" size={13} />
              {project.task_count} task{project.task_count === 1 ? "" : "s"}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
