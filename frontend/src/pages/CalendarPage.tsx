import { useMemo, useState } from "react";

import { Icon } from "@/components/icons";
import { Button, LoadingRow, PageHeader, SegmentedControl } from "@/components/ui";
import type { Occurrence } from "@/features/calendar/api";
import {
  addDays,
  addMonths,
  fmtMonthYear,
  fmtWeekRange,
  monthMatrix,
  startOfWeek,
} from "@/features/calendar/dateUtils";
import { EventModal } from "@/features/calendar/EventModal";
import { MonthView } from "@/features/calendar/MonthView";
import { useOccurrences } from "@/features/calendar/queries";
import { WeekView } from "@/features/calendar/WeekView";

type View = "month" | "week";
type ModalState =
  | { eventId: number | null; defaultDate?: Date; occurrence?: Occurrence }
  | null;

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

  const shift = (d: -1 | 1) =>
    setAnchor((c) => (view === "month" ? addMonths(c, d) : addDays(c, d * 7)));

  return (
    <div>
      <PageHeader
        title={view === "month" ? fmtMonthYear(anchor) : fmtWeekRange(anchor)}
        subtitle={
          <span className="inline-flex items-center gap-1">
            <button
              type="button"
              onClick={() => shift(-1)}
              className="grid h-7 w-7 place-items-center rounded-lg text-faint transition hover:bg-line/[0.06] hover:text-content"
              aria-label="Previous"
            >
              <Icon name="chevronLeft" size={16} />
            </button>
            <button
              type="button"
              onClick={() => setAnchor(new Date())}
              className="rounded-lg border border-line/[0.12] px-2.5 py-1 text-xs font-medium text-muted transition hover:border-brand/40 hover:text-content"
            >
              Today
            </button>
            <button
              type="button"
              onClick={() => shift(1)}
              className="grid h-7 w-7 place-items-center rounded-lg text-faint transition hover:bg-line/[0.06] hover:text-content"
              aria-label="Next"
            >
              <Icon name="chevronRight" size={16} />
            </button>
          </span>
        }
        actions={
          <>
            <SegmentedControl
              value={view}
              onChange={setView}
              options={[
                { value: "month", label: "month", icon: "calendar" },
                { value: "week", label: "week", icon: "layers" },
              ]}
            />
            <Button variant="primary" icon="plus" onClick={() => setModal({ eventId: null })}>
              Event
            </Button>
          </>
        }
      />

      {isLoading && <LoadingRow />}

      {view === "month" ? (
        <MonthView
          anchor={anchor}
          occurrences={occurrences}
          onPickDay={(day) => setModal({ eventId: null, defaultDate: day })}
          onOpenOccurrence={(occ) => setModal({ eventId: occ.event_id, occurrence: occ })}
        />
      ) : (
        <WeekView
          anchor={anchor}
          occurrences={occurrences}
          onPickDay={(day) => setModal({ eventId: null, defaultDate: day })}
          onOpenOccurrence={(occ) => setModal({ eventId: occ.event_id, occurrence: occ })}
        />
      )}

      {modal && (
        <EventModal
          eventId={modal.eventId}
          defaultDate={modal.defaultDate}
          occurrence={modal.occurrence}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}
