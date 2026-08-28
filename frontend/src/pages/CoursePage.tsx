import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import * as ln from "@/features/learning/api";
import { ReviewSession } from "@/features/learning/ReviewSession";
import {
  useCourse,
  useFlashcards,
  useLearningMutation,
  useNotes,
} from "@/features/learning/queries";

const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm outline-none " +
  "focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900";

export default function CoursePage() {
  const params = useParams<{ courseId: string }>();
  const courseId = Number(params.courseId);
  const { data: course, isLoading } = useCourse(courseId);
  const { data: flashcards = [] } = useFlashcards(courseId);
  const { data: notes = [] } = useNotes(courseId);
  const [reviewing, setReviewing] = useState(false);

  const addLesson = useLearningMutation((title: string) => ln.addLesson(courseId, title));
  const toggleLesson = useLearningMutation(
    ({ id, completed }: { id: number; completed: boolean }) =>
      ln.updateLesson(id, { completed }),
  );
  const removeLesson = useLearningMutation((id: number) => ln.deleteLesson(id));
  const addCard = useLearningMutation((input: { front: string; back: string }) =>
    ln.addFlashcard(courseId, input),
  );
  const removeCard = useLearningMutation((id: number) => ln.deleteFlashcard(id));
  const addNote = useLearningMutation((body: string) => ln.addNote(courseId, body));
  const removeNote = useLearningMutation((id: number) => ln.deleteNote(id));

  const [lessonTitle, setLessonTitle] = useState("");
  const [front, setFront] = useState("");
  const [back, setBack] = useState("");
  const [noteBody, setNoteBody] = useState("");

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!course) return <p className="text-sm text-rose-600">Course not found.</p>;

  function submitCard(event: FormEvent): void {
    event.preventDefault();
    if (front.trim() && back.trim()) {
      addCard.mutate(
        { front: front.trim(), back: back.trim() },
        { onSuccess: () => {
            setFront("");
            setBack("");
          } },
      );
    }
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/learning" className="text-xs text-slate-400 hover:underline">
            ← Learning
          </Link>
          <h2 className="text-xl font-semibold">{course.title}</h2>
          <p className="text-sm text-slate-500">
            {Math.round(course.progress * 100)}% · {course.flashcards_due} card
            {course.flashcards_due === 1 ? "" : "s"} due
          </p>
        </div>
        {course.flashcards_due > 0 && (
          <button
            type="button"
            onClick={() => setReviewing(true)}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            Review ({course.flashcards_due})
          </button>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-medium text-slate-500">Lessons</h3>
          <ul className="space-y-1.5">
            {course.lessons.map((lesson) => (
              <li key={lesson.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={lesson.completed}
                  onChange={(e) =>
                    toggleLesson.mutate({ id: lesson.id, completed: e.target.checked })
                  }
                />
                <span className={lesson.completed ? "text-slate-400 line-through" : ""}>
                  {lesson.title}
                </span>
                <button
                  type="button"
                  onClick={() => removeLesson.mutate(lesson.id)}
                  className="ml-auto text-slate-300 hover:text-rose-500"
                  aria-label="Delete lesson"
                >
                  ✕
                </button>
              </li>
            ))}
            {course.lessons.length === 0 && (
              <li className="text-sm text-slate-400">No lessons yet.</li>
            )}
          </ul>
          <form
            className="mt-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (lessonTitle.trim())
                addLesson.mutate(lessonTitle.trim(), { onSuccess: () => setLessonTitle("") });
            }}
          >
            <input
              className={inputClass}
              placeholder="+ Add lesson"
              value={lessonTitle}
              onChange={(e) => setLessonTitle(e.target.value)}
            />
          </form>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-medium text-slate-500">
            Flashcards ({flashcards.length})
          </h3>
          <ul className="space-y-1.5">
            {flashcards.map((card) => (
              <li
                key={card.id}
                className="flex items-center justify-between rounded-md bg-slate-50 px-2 py-1 text-sm dark:bg-slate-800"
              >
                <span className="truncate">
                  {card.front} <span className="text-slate-400">→ {card.back}</span>
                </span>
                <button
                  type="button"
                  onClick={() => removeCard.mutate(card.id)}
                  className="text-slate-300 hover:text-rose-500"
                  aria-label="Delete flashcard"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
          <form onSubmit={submitCard} className="mt-2 space-y-2">
            <input
              className={inputClass}
              placeholder="Front"
              value={front}
              onChange={(e) => setFront(e.target.value)}
            />
            <div className="flex gap-2">
              <input
                className={inputClass}
                placeholder="Back"
                value={back}
                onChange={(e) => setBack(e.target.value)}
              />
              <button
                type="submit"
                className="shrink-0 rounded-md bg-slate-100 px-3 py-1 text-sm font-medium hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
              >
                Add
              </button>
            </div>
          </form>
        </section>
      </div>

      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <h3 className="mb-3 text-sm font-medium text-slate-500">Notes</h3>
        <ul className="space-y-1.5">
          {notes.map((note) => (
            <li
              key={note.id}
              className="flex items-start justify-between gap-2 rounded-md bg-slate-50 px-2 py-1 text-sm dark:bg-slate-800"
            >
              <span className="whitespace-pre-wrap">{note.body}</span>
              <button
                type="button"
                onClick={() => removeNote.mutate(note.id)}
                className="text-slate-300 hover:text-rose-500"
                aria-label="Delete note"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
        <form
          className="mt-2 flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            if (noteBody.trim())
              addNote.mutate(noteBody.trim(), { onSuccess: () => setNoteBody("") });
          }}
        >
          <input
            className={inputClass}
            placeholder="Add a note"
            value={noteBody}
            onChange={(e) => setNoteBody(e.target.value)}
          />
          <button
            type="submit"
            className="shrink-0 rounded-md bg-slate-100 px-3 py-1 text-sm font-medium hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
          >
            Add
          </button>
        </form>
      </section>

      {reviewing && (
        <ReviewSession courseId={courseId} onClose={() => setReviewing(false)} />
      )}
    </div>
  );
}
