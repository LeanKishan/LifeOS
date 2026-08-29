import { useEffect, useMemo, useState, type FormEvent } from "react";

import { Modal } from "@/components/Modal";
import type { EventInput, Occurrence } from "@/features/calendar/api";
import { toDateInput, toLocalInput } from "@/features/calendar/dateUtils";
import {
  useCreateEvent,
  useDeleteEvent,
  useDeleteOverride,
  useEvent,
  useOverrides,
  useUpdateEvent,
  useUpsertOverride,
} from "@/features/calendar/queries";

const FREQS = ["none", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"] as const;
type Freq = (typeof FREQS)[number];
const FREQ_LABEL: Record<Freq, string> = {
  none: "Does not repeat",
  DAILY: "Daily",
  WEEKLY: "Weekly",
  MONTHLY: "Monthly",
  YEARLY: "Yearly",
};

const inputClass = "field-input";



function parseRecurrence(rule: string | null): { freq: Freq; until: string } {
  if (!rule) return { freq: "none", until: "" };
  const freqMatch = /FREQ=(DAILY|WEEKLY|MONTHLY|YEARLY)/.exec(rule);
  const untilMatch = /UNTIL=(\d{4})(\d{2})(\d{2})/.exec(rule);
  return {
    freq: (freqMatch?.[1] as Freq) ?? "none",
    until: untilMatch ? `${untilMatch[1]}-${untilMatch[2]}-${untilMatch[3]}` : "",
  };
}

function buildRecurrence(freq: Freq, until: string): string | null {
  if (freq === "none") return null;
  let rule = `FREQ=${freq}`;
  if (until) rule += `;UNTIL=${until.replace(/-/g, "")}T000000Z`;
  return rule;
}

export function EventModal({
  eventId,
  defaultDate,
  occurrence,
  onClose,
}: {
  eventId: number | null;
  defaultDate?: Date;
  occurrence?: Occurrence;
  onClose: () => void;
}) {
  const editing = eventId !== null;
  const { data: existing, isLoading } = useEvent(eventId);
  const create = useCreateEvent();
  const update = useUpdateEvent();
  const remove = useDeleteEvent();

  const initial = useMemo(() => {
    const base = defaultDate ?? new Date();
    const start = new Date(base);
    if (!defaultDate) start.setMinutes(0, 0, 0);
    else start.setHours(9, 0, 0, 0);
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    return { start, end };
  }, [defaultDate]);

  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [allDay, setAllDay] = useState(false);
  const [start, setStart] = useState(toLocalInput(initial.start));
  const [end, setEnd] = useState(toLocalInput(initial.end));
  const [startDate, setStartDate] = useState(toDateInput(initial.start));
  const [endDate, setEndDate] = useState(toDateInput(initial.end));
  const [freq, setFreq] = useState<Freq>("none");
  const [until, setUntil] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!existing) return;
    const s = new Date(existing.start_at);
    const e = new Date(existing.end_at);
    setTitle(existing.title);
    setLocation(existing.location ?? "");
    setDescription(existing.description ?? "");
    setAllDay(existing.all_day);
    setStart(toLocalInput(s));
    setEnd(toLocalInput(e));
    setStartDate(toDateInput(s));
    setEndDate(toDateInput(e));
    const parsed = parseRecurrence(existing.recurrence);
    setFreq(parsed.freq);
    setUntil(parsed.until);
  }, [existing]);

  function submit(event: FormEvent): void {
    event.preventDefault();
    setError(null);

    const startIso = allDay
      ? new Date(`${startDate}T00:00`).toISOString()
      : new Date(start).toISOString();
    const endIso = allDay
      ? new Date(`${endDate}T00:00`).toISOString()
      : new Date(end).toISOString();

    if (new Date(endIso) < new Date(startIso)) {
      setError("End is before start.");
      return;
    }

    const payload: EventInput = {
      title: title.trim(),
      location: location.trim() || null,
      description: description.trim() || null,
      start_at: startIso,
      end_at: endIso,
      all_day: allDay,
      recurrence: buildRecurrence(freq, until),
    };

    const onDone = { onSuccess: onClose, onError: () => setError("Could not save the event.") };
    if (editing && eventId !== null) update.mutate({ id: eventId, input: payload }, onDone);
    else create.mutate(payload, onDone);
  }

  const pending = create.isPending || update.isPending;

  return (
    <Modal title={editing ? "Edit event" : "New event"} onClose={onClose}>
      {editing && isLoading ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : (
        <>
          {occurrence?.is_recurring && eventId !== null && (
            <OccurrenceOverridePanel
              eventId={eventId}
              occurrence={occurrence}
              onDone={onClose}
            />
          )}
          <form onSubmit={submit} className="space-y-3">
          {error && (
            <p role="alert" className="rounded-md border border-rose-500/25 bg-rose-500/10 px-3 py-2.5 text-sm text-rose-300">
              {error}
            </p>
          )}
          <input
            className={inputClass}
            placeholder="Title"
            value={title}
            required
            onChange={(e) => setTitle(e.target.value)}
          />

          <label className="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={allDay} onChange={(e) => setAllDay(e.target.checked)} />
            All day
          </label>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {allDay ? (
              <>
                <label className="block">
                  <span className="mb-1 block text-xs text-muted">Start</span>
                  <input type="date" className={inputClass} value={startDate} onChange={(e) => setStartDate(e.target.value)} />
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs text-muted">End</span>
                  <input type="date" className={inputClass} value={endDate} onChange={(e) => setEndDate(e.target.value)} />
                </label>
              </>
            ) : (
              <>
                <label className="block">
                  <span className="mb-1 block text-xs text-muted">Start</span>
                  <input type="datetime-local" className={inputClass} value={start} onChange={(e) => setStart(e.target.value)} />
                </label>
                <label className="block">
                  <span className="mb-1 block text-xs text-muted">End</span>
                  <input type="datetime-local" className={inputClass} value={end} onChange={(e) => setEnd(e.target.value)} />
                </label>
              </>
            )}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1 block text-xs text-muted">Repeat</span>
              <select className={inputClass} value={freq} onChange={(e) => setFreq(e.target.value as Freq)}>
                {FREQS.map((value) => (
                  <option key={value} value={value}>
                    {FREQ_LABEL[value]}
                  </option>
                ))}
              </select>
            </label>
            {freq !== "none" && (
              <label className="block">
                <span className="mb-1 block text-xs text-muted">Until (optional)</span>
                <input type="date" className={inputClass} value={until} onChange={(e) => setUntil(e.target.value)} />
              </label>
            )}
          </div>

          <input
            className={inputClass}
            placeholder="Location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
          <textarea
            className={inputClass}
            rows={2}
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={pending}
              className="rounded-md btn-primary btn-md disabled:opacity-50"
            >
              {pending ? "Saving…" : editing ? "Save" : "Create"}
            </button>
            {editing && eventId !== null && (
              <button
                type="button"
                onClick={() => remove.mutate(eventId, { onSuccess: onClose })}
                className="text-xs font-medium text-rose-400 hover:underline"
              >
                Delete event
              </button>
            )}
          </div>
          </form>
        </>
      )}
    </Modal>
  );
}

function OccurrenceOverridePanel({
  eventId,
  occurrence,
  onDone,
}: {
  eventId: number;
  occurrence: Occurrence;
  onDone: () => void;
}) {
  const [start, setStart] = useState(toLocalInput(new Date(occurrence.start_at)));
  const [end, setEnd] = useState(toLocalInput(new Date(occurrence.end_at)));
  const upsert = useUpsertOverride();
  const removeOverride = useDeleteOverride();
  const { data: overrides = [] } = useOverrides(occurrence.overridden ? eventId : null);
  const thisOverride = overrides.find(
    (o) => o.occurrence_start === occurrence.occurrence_start,
  );

  const label = new Date(occurrence.occurrence_start).toLocaleDateString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="mb-3 rounded-md border border-amber-500/25 bg-amber-500/10 p-3 text-sm">
      <p className="mb-2 font-medium text-amber-300">
        This occurrence · {label}
        {occurrence.overridden && " (changed)"}
      </p>
      <div className="grid grid-cols-2 gap-2">
        <label className="block">
          <span className="mb-1 block text-xs text-amber-300/80">Start</span>
          <input
            type="datetime-local"
            className={inputClass}
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs text-amber-300/80">End</span>
          <input
            type="datetime-local"
            className={inputClass}
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={upsert.isPending}
          onClick={() =>
            upsert.mutate(
              {
                id: eventId,
                input: {
                  occurrence_start: occurrence.occurrence_start,
                  start_at: new Date(start).toISOString(),
                  end_at: new Date(end).toISOString(),
                },
              },
              { onSuccess: onDone },
            )
          }
          className="btn-primary btn-sm"
        >
          Reschedule this one
        </button>
        <button
          type="button"
          disabled={upsert.isPending}
          onClick={() =>
            upsert.mutate(
              { id: eventId, input: { occurrence_start: occurrence.occurrence_start, canceled: true } },
              { onSuccess: onDone },
            )
          }
          className="text-xs font-medium text-rose-400 hover:underline"
        >
          Skip this occurrence
        </button>
        {thisOverride && (
          <button
            type="button"
            disabled={removeOverride.isPending}
            onClick={() => removeOverride.mutate(thisOverride.id, { onSuccess: onDone })}
            className="text-xs font-medium text-muted hover:underline"
          >
            Restore to series
          </button>
        )}
      </div>
    </div>
  );
}
