import type { Occurrence } from "@/features/calendar/api";
import { fmtTime, sameDay, weekDays } from "@/features/calendar/dateUtils";
import { cn } from "@/lib/cn";

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
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-7">
      {days.map((day) => {
        const dayOcc = occurrences
          .filter((o) => sameDay(new Date(o.start_at), day))
          .sort((a, b) => a.start_at.localeCompare(b.start_at));

        return (
          <div key={day.toISOString()} className="surface-card p-3">
            <button
              type="button"
              onClick={() => onPickDay(day)}
              className="mb-2 block text-left text-xs font-medium"
            >
              <span className="text-faint">
                {day.toLocaleDateString([], { weekday: "short" })}
              </span>{" "}
              <span
                className={cn(
                  sameDay(day, today) ? "font-bold text-brand-hi" : "text-content",
                )}
              >
                {day.getDate()}
              </span>
            </button>
            <div className="space-y-1.5">
              {dayOcc.map((o, i) => (
                <button
                  key={`${o.event_id}-${i}`}
                  type="button"
                  onClick={() => onOpenOccurrence(o)}
                  className="block w-full rounded-md border border-brand/20 bg-brand/10 px-2 py-1.5 text-left text-[11px] text-brand-hi transition hover:bg-brand/20"
                >
                  <div className="font-medium text-content">
                    {o.title}
                    {o.overridden && <span title="Changed"> ✎</span>}
                  </div>
                  {!o.all_day && (
                    <div className="tabular-nums opacity-80">
                      {fmtTime(new Date(o.start_at))}
                    </div>
                  )}
                </button>
              ))}
              {dayOcc.length === 0 && <p className="text-[11px] text-faint">—</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
