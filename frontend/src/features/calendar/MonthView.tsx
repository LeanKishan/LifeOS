import type { Occurrence } from "@/features/calendar/api";
import { fmtTime, monthMatrix, sameDay } from "@/features/calendar/dateUtils";
import { cn } from "@/lib/cn";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function MonthView({
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
  const days = monthMatrix(anchor);
  const today = new Date();

  return (
    <div className="surface-card overflow-hidden p-0">
      <div className="grid grid-cols-7 border-b border-line/[0.08] bg-surface-2 text-[11px] font-semibold uppercase tracking-wide text-faint">
        {WEEKDAYS.map((label) => (
          <div key={label} className="px-2 py-2 text-center">
            {label}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {days.map((day) => {
          const inMonth = day.getMonth() === anchor.getMonth();
          const dayOcc = occurrences
            .filter((o) => sameDay(new Date(o.start_at), day))
            .sort((a, b) => a.start_at.localeCompare(b.start_at));

          return (
            <div
              key={day.toISOString()}
              className={cn(
                "min-h-[6.5rem] border-b border-r border-line/[0.05] p-1.5",
                !inMonth && "bg-line/[0.02]",
              )}
            >
              <button
                type="button"
                onClick={() => onPickDay(day)}
                className={cn(
                  "mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs transition",
                  sameDay(day, today)
                    ? "bg-brand font-bold text-[#04140d]"
                    : inMonth
                      ? "text-content hover:bg-line/[0.08]"
                      : "text-faint",
                )}
              >
                {day.getDate()}
              </button>
              <div className="space-y-1">
                {dayOcc.slice(0, 3).map((o, i) => (
                  <button
                    key={`${o.event_id}-${i}`}
                    type="button"
                    onClick={() => onOpenOccurrence(o)}
                    className="block w-full truncate rounded-md border border-brand/20 bg-brand/10 px-1.5 py-0.5 text-left text-[11px] text-brand-hi transition hover:bg-brand/20"
                  >
                    {!o.all_day && (
                      <span className="tabular-nums opacity-70">
                        {fmtTime(new Date(o.start_at))}{" "}
                      </span>
                    )}
                    {o.title}
                    {o.overridden && <span title="Changed"> ✎</span>}
                  </button>
                ))}
                {dayOcc.length > 3 && (
                  <div className="px-1 text-[10px] text-faint">+{dayOcc.length - 3} more</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
