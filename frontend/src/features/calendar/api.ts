import { api } from "@/lib/api";

export interface Reminder {
  id: number;
  event_id: number;
  minutes_before: number;
}

export interface CalendarEvent {
  id: number;
  title: string;
  description: string | null;
  location: string | null;
  start_at: string;
  end_at: string;
  all_day: boolean;
  recurrence: string | null;
  project_id: number | null;
  task_id: number | null;
  application_id: number | null;
  reminders: Reminder[];
  created_at: string;
}

export interface Occurrence {
  event_id: number;
  title: string;
  description: string | null;
  location: string | null;
  all_day: boolean;
  is_recurring: boolean;
  start_at: string;
  end_at: string;
}

export interface EventInput {
  title: string;
  description?: string | null;
  location?: string | null;
  start_at: string;
  end_at: string;
  all_day?: boolean;
  recurrence?: string | null;
}

const BASE = "/calendar";

export async function listOccurrences(from: string, to: string): Promise<Occurrence[]> {
  const { data } = await api.get<Occurrence[]>(`${BASE}/occurrences`, {
    params: { from, to },
  });
  return data;
}

export async function getEvent(eventId: number): Promise<CalendarEvent> {
  const { data } = await api.get<CalendarEvent>(`${BASE}/events/${eventId}`);
  return data;
}

export async function createEvent(input: EventInput): Promise<CalendarEvent> {
  const { data } = await api.post<CalendarEvent>(`${BASE}/events`, input);
  return data;
}

export async function updateEvent(
  eventId: number,
  input: Partial<EventInput>,
): Promise<CalendarEvent> {
  const { data } = await api.patch<CalendarEvent>(`${BASE}/events/${eventId}`, input);
  return data;
}

export async function deleteEvent(eventId: number): Promise<void> {
  await api.delete(`${BASE}/events/${eventId}`);
}
