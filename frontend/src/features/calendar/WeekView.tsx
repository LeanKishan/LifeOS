import type { Occurrence } from "@/features/calendar/api";
import { fmtTime, sameDay, weekDays } from "@/features/calendar/dateUtils";

export function WeekView({
  anchor,
  occurrences,
  onPickDay,
  onOpenOccurrence,
}: {
  anchor: Date;
  occurrences: Occurrence[];
  onPickDay: (day: Date) => void;
  onOpenOccurrence: (occurrence: Occurrence) => void;
}) {
  const days = weekDays(anchor);
  const today = new Date();

  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-7">
      {days.map((day) => {
        const dayOccurrences = occurrences
          .filter((occurrence) => sameDay(new Date(occurrence.start_at), day))
          .sort((a, b) => a.start_at.localeCompare(b.start_at));

        return (
          <div
            key={day.toISOString()}
            className="rounded-lg border border-slate-200 p-2 dark:border-slate-800"
          >
            <button
              type="button"
              onClick={() => onPickDay(day)}
              className="mb-2 block text-left text-xs font-medium"
            >
              <span className="text-slate-400">
                {day.toLocaleDateString([], { weekday: "short" })}
              </span>{" "}
              <span
                className={
                  sameDay(day, today) ? "font-semibold text-emerald-600" : "text-slate-600 dark:text-slate-300"
                }
              >
                {day.getDate()}
              </span>
            </button>
            <div className="space-y-1">
              {dayOccurrences.map((occurrence, index) => (
                <button
                  key={`${occurrence.event_id}-${index}`}
                  type="button"
                  onClick={() => onOpenOccurrence(occurrence)}
                  className="block w-full rounded bg-emerald-100 px-1.5 py-1 text-left text-[11px] text-emerald-800 hover:bg-emerald-200 dark:bg-emerald-950 dark:text-emerald-300"
                >
                  <div className="font-medium">
                    {occurrence.title}
                    {occurrence.overridden && (
                      <span title="This occurrence was changed"> ✎</span>
                    )}
                  </div>
                  {!occurrence.all_day && (
                    <div className="tabular-nums text-emerald-600 dark:text-emerald-500">
                      {fmtTime(new Date(occurrence.start_at))}
                    </div>
                  )}
                </button>
              ))}
              {dayOccurrences.length === 0 && (
                <p className="text-[11px] text-slate-300">—</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
