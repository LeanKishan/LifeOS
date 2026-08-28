import { useMemo, useState } from "react";

import { EventModal } from "@/features/calendar/EventModal";
import { MonthView } from "@/features/calendar/MonthView";
import { WeekView } from "@/features/calendar/WeekView";
import {
  addDays,
  addMonths,
  fmtMonthYear,
  fmtWeekRange,
  monthMatrix,
  startOfWeek,
} from "@/features/calendar/dateUtils";
import { useOccurrences } from "@/features/calendar/queries";

type View = "month" | "week";
type ModalState = { eventId: number | null; defaultDate?: Date } | null;

export default function CalendarPage() {
  const [view, setView] = useState<View>("month");
  const [anchor, setAnchor] = useState<Date>(() => new Date());
  const [modal, setModal] = useState<ModalState>(null);

  const range = useMemo(() => {
    if (view === "month") {
      const cells = monthMatrix(anchor);
      return { from: cells[0], to: addDays(cells[cells.length - 1], 1) };
    }
    const start = startOfWeek(anchor);
    return { from: start, to: addDays(start, 7) };
  }, [view, anchor]);

  const { data: occurrences = [], isLoading } = useOccurrences(
    range.from.toISOString(),
    range.to.toISOString(),
  );

  function shift(direction: -1 | 1): void {
    setAnchor((current) =>
      view === "month" ? addMonths(current, direction) : addDays(current, direction * 7),
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold">
            {view === "month" ? fmtMonthYear(anchor) : fmtWeekRange(anchor)}
          </h2>
          <div className="flex items-center gap-1 text-sm">
            <button
              type="button"
              onClick={() => shift(-1)}
              className="rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Previous"
            >
              ◀
            </button>
            <button
              type="button"
              onClick={() => setAnchor(new Date())}
              className="rounded border border-slate-300 px-2 py-1 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              Today
            </button>
            <button
              type="button"
              onClick={() => shift(1)}
              className="rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Next"
            >
              ▶
            </button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-slate-300 text-sm dark:border-slate-700">
            {(["month", "week"] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setView(value)}
                className={`px-3 py-1.5 capitalize ${
                  view === value ? "bg-slate-100 font-medium dark:bg-slate-800" : "text-slate-500"
                }`}
              >
                {value}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setModal({ eventId: null })}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
          >
            + Event
          </button>
        </div>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {view === "month" ? (
        <MonthView
          anchor={anchor}
          occurrences={occurrences}
          onPickDay={(day) => setModal({ eventId: null, defaultDate: day })}
          onOpenEvent={(eventId) => setModal({ eventId })}
        />
      ) : (
        <WeekView
          anchor={anchor}
          occurrences={occurrences}
          onPickDay={(day) => setModal({ eventId: null, defaultDate: day })}
          onOpenEvent={(eventId) => setModal({ eventId })}
        />
      )}

      {modal && (
        <EventModal
          eventId={modal.eventId}
          defaultDate={modal.defaultDate}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}
