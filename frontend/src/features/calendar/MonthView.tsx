import type { Occurrence } from "@/features/calendar/api";
import { fmtTime, monthMatrix, sameDay } from "@/features/calendar/dateUtils";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function MonthView({
  anchor,
  occurrences,
  onPickDay,
  onOpenEvent,
}: {
  anchor: Date;
  occurrences: Occurrence[];
  onPickDay: (day: Date) => void;
  onOpenEvent: (eventId: number) => void;
}) {
  const days = monthMatrix(anchor);
  const today = new Date();

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
      <div className="grid grid-cols-7 bg-slate-50 text-xs font-medium text-slate-500 dark:bg-slate-900">
        {WEEKDAYS.map((label) => (
          <div key={label} className="px-2 py-1.5 text-center">
            {label}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {days.map((day) => {
          const inMonth = day.getMonth() === anchor.getMonth();
          const dayOccurrences = occurrences
            .filter((occurrence) => sameDay(new Date(occurrence.start_at), day))
            .sort((a, b) => a.start_at.localeCompare(b.start_at));

          return (
            <div
              key={day.toISOString()}
              className={`min-h-24 border-b border-r border-slate-100 p-1 dark:border-slate-800/70 ${
                inMonth ? "" : "bg-slate-50/60 dark:bg-slate-950"
              }`}
            >
              <button
                type="button"
                onClick={() => onPickDay(day)}
                className={`mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                  sameDay(day, today)
                    ? "bg-emerald-600 font-semibold text-white"
                    : inMonth
                      ? "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                      : "text-slate-400"
                }`}
              >
                {day.getDate()}
              </button>
              <div className="space-y-0.5">
                {dayOccurrences.slice(0, 3).map((occurrence, index) => (
                  <button
                    key={`${occurrence.event_id}-${index}`}
                    type="button"
                    onClick={() => onOpenEvent(occurrence.event_id)}
                    className="block w-full truncate rounded bg-emerald-100 px-1 py-0.5 text-left text-[11px] text-emerald-800 hover:bg-emerald-200 dark:bg-emerald-950 dark:text-emerald-300"
                  >
                    {!occurrence.all_day && (
                      <span className="tabular-nums">{fmtTime(new Date(occurrence.start_at))} </span>
                    )}
                    {occurrence.title}
                  </button>
                ))}
                {dayOccurrences.length > 3 && (
                  <div className="px-1 text-[10px] text-slate-400">
                    +{dayOccurrences.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
