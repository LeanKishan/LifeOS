import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Icon } from "@/components/icons";
import { Button, EmptyState, Input, LoadingRow, PageHeader } from "@/components/ui";
import * as ln from "@/features/learning/api";
import { ReviewSession } from "@/features/learning/ReviewSession";
import { useCourses, useLearningMutation, useReviewCount } from "@/features/learning/queries";

export default function LearningPage() {
  const { data: courses = [], isLoading } = useCourses();
  const { data: due = [] } = useReviewCount();
  const create = useLearningMutation(ln.createCourse);
  const [title, setTitle] = useState("");
  const [reviewing, setReviewing] = useState(false);

  function submit(event: FormEvent): void {
    event.preventDefault();
    const value = title.trim();
    if (value) create.mutate({ title: value }, { onSuccess: () => setTitle("") });
  }

  return (
    <div>
      <PageHeader
        title="Learning"
        subtitle="Courses, lessons, and spaced-repetition flashcards."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <form onSubmit={submit} className="flex gap-2">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="New course"
                className="w-40 sm:w-48"
              />
              <Button type="submit" variant="secondary" icon="plus" loading={create.isPending}>
                Add
              </Button>
            </form>
            <Button variant="primary" icon="target" onClick={() => setReviewing(true)}>
              Review{due.length > 0 ? ` · ${due.length}` : ""}
            </Button>
          </div>
        }
      />

      {isLoading && <LoadingRow />}
      {!isLoading && courses.length === 0 && (
        <EmptyState
          icon="book"
          title="No courses yet"
          description="Add a course, then break it into lessons and flashcards."
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {courses.map((course, i) => (
          <Link
            key={course.id}
            to={`/learning/courses/${course.id}`}
            className={`surface-card card-hover group animate-fade-in-up stagger-${Math.min(i + 1, 6)} p-5`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="font-semibold text-content">{course.title}</div>
              <Icon
                name="arrowRight"
                size={16}
                className="text-faint transition group-hover:translate-x-0.5 group-hover:text-brand-hi"
              />
            </div>
            <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-line/[0.08]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-hi to-brand"
                style={{ width: `${Math.round(course.progress * 100)}%` }}
              />
            </div>
            <div className="mt-2 flex justify-between text-xs text-faint">
              <span>
                {course.lessons_completed}/{course.lesson_count} lessons
              </span>
              {course.flashcards_due > 0 && (
                <span className="text-brand-hi">{course.flashcards_due} due</span>
              )}
            </div>
          </Link>
        ))}
      </div>

      {reviewing && <ReviewSession onClose={() => setReviewing(false)} />}
    </div>
  );
}
