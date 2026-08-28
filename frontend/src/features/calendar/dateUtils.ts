const pad = (n: number): string => String(n).padStart(2, "0");

export function startOfDay(date: Date): Date {
  const copy = new Date(date);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

export function addDays(date: Date, days: number): Date {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

export function addMonths(date: Date, months: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + months, 1);
}

export function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

/** Sunday-based start of the week containing `date`. */
export function startOfWeek(date: Date): Date {
  const day = startOfDay(date);
  return addDays(day, -day.getDay());
}

/** 42 consecutive days (6 weeks) covering the month that `anchor` is in. */
export function monthMatrix(anchor: Date): Date[] {
  const firstOfMonth = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const start = startOfWeek(firstOfMonth);
  return Array.from({ length: 42 }, (_, i) => addDays(start, i));
}

export function weekDays(anchor: Date): Date[] {
  const start = startOfWeek(anchor);
  return Array.from({ length: 7 }, (_, i) => addDays(start, i));
}

/** Local-time value for an <input type="datetime-local">. */
export function toLocalInput(date: Date): string {
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

export function toDateInput(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function fmtTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function fmtMonthYear(date: Date): string {
  return date.toLocaleDateString([], { month: "long", year: "numeric" });
}

export function fmtWeekRange(anchor: Date): string {
  const days = weekDays(anchor);
  const first = days[0];
  const last = days[6];
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  return `${first.toLocaleDateString([], opts)} – ${last.toLocaleDateString([], opts)}, ${last.getFullYear()}`;
}
