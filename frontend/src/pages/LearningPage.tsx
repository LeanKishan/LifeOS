import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

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
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Learning</h2>
        <div className="flex items-center gap-2">
          <form onSubmit={submit} className="flex gap-2">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="New course"
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
            />
            <button
              type="submit"
              className="rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
            >
              Add
            </button>
          </form>
          <button
            type="button"
            onClick={() => setReviewing(true)}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            Review{due.length > 0 ? ` (${due.length})` : ""}
          </button>
        </div>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {!isLoading && courses.length === 0 && (
        <p className="text-sm text-slate-500">No courses yet — add one to start.</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {courses.map((course) => (
          <Link
            key={course.id}
            to={`/learning/courses/${course.id}`}
            className="rounded-lg border border-slate-200 bg-white p-4 hover:border-emerald-400 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="font-medium">{course.title}</div>
            <div className="mt-3 h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className="h-2 rounded-full bg-emerald-500"
                style={{ width: `${Math.round(course.progress * 100)}%` }}
              />
            </div>
            <div className="mt-2 flex justify-between text-xs text-slate-400">
              <span>
                {course.lessons_completed}/{course.lesson_count} lessons
              </span>
              {course.flashcards_due > 0 && <span>{course.flashcards_due} due</span>}
            </div>
          </Link>
        ))}
      </div>

      {reviewing && <ReviewSession onClose={() => setReviewing(false)} />}
    </div>
  );
}
