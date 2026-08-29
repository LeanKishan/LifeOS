import { useEffect, useState } from "react";

import * as ln from "@/features/learning/api";
import type { Flashcard } from "@/features/learning/api";
import { useLearningMutation } from "@/features/learning/queries";

const GRADES: { label: string; quality: number; className: string }[] = [
  { label: "Again", quality: 1, className: "bg-rose-600 hover:bg-rose-700" },
  { label: "Hard", quality: 3, className: "bg-amber-600 hover:bg-amber-700" },
  { label: "Good", quality: 4, className: "bg-brand text-[#04140d] hover:bg-brand-lo" },
  { label: "Easy", quality: 5, className: "bg-sky-600 hover:bg-sky-700" },
];

export function ReviewSession({
  courseId,
  onClose,
}: {
  courseId?: number;
  onClose: () => void;
}) {
  const [queue, setQueue] = useState<Flashcard[] | null>(null);
  const [index, setIndex] = useState(0);
  const [showBack, setShowBack] = useState(false);
  const review = useLearningMutation(
    ({ id, quality }: { id: number; quality: number }) => ln.reviewFlashcard(id, quality),
  );

  useEffect(() => {
    let active = true;
    ln.reviewQueue(courseId).then((cards) => {
      if (active) setQueue(cards);
    });
    return () => {
      active = false;
    };
  }, [courseId]);

  const card = queue?.[index] ?? null;
  const done = queue !== null && index >= queue.length;

  function grade(quality: number): void {
    if (!card) return;
    review.mutate({ id: card.id, quality });
    setShowBack(false);
    setIndex((current) => current + 1);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="w-full max-w-lg rounded-xl bg-surface p-6 shadow-xl "
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Flashcard review"
      >
        <div className="mb-4 flex items-center justify-between text-sm text-muted">
          <span>
            {queue === null
              ? "Loading…"
              : done
                ? "Session complete"
                : `Card ${index + 1} of ${queue.length}`}
          </span>
          <button type="button" onClick={onClose} aria-label="Close" className="hover:text-content">
            ✕
          </button>
        </div>

        {queue !== null && queue.length === 0 && (
          <p className="py-10 text-center text-muted">Nothing due right now. 🎉</p>
        )}

        {done && queue.length > 0 && (
          <p className="py-10 text-center text-content">
            Reviewed {queue.length} card{queue.length === 1 ? "" : "s"}. Nice work.
          </p>
        )}

        {card && !done && (
          <>
            <div className="min-h-32 rounded-lg border border-line/[0.08] p-5 text-center ">
              <p className="whitespace-pre-wrap text-lg">{card.front}</p>
              {showBack && (
                <>
                  <hr className="my-4 border-line/[0.08] " />
                  <p className="whitespace-pre-wrap text-content">
                    {card.back}
                  </p>
                </>
              )}
            </div>

            {showBack ? (
              <div className="mt-4 grid grid-cols-4 gap-2">
                {GRADES.map((grade_) => (
                  <button
                    key={grade_.label}
                    type="button"
                    onClick={() => grade(grade_.quality)}
                    className={`rounded-md px-2 py-2 text-sm font-medium text-white ${grade_.className}`}
                  >
                    {grade_.label}
                  </button>
                ))}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setShowBack(true)}
                className="mt-4 w-full rounded-md bg-line/[0.08] px-4 py-2 text-sm font-medium hover:bg-line/[0.12] "
              >
                Show answer
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
