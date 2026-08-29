import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as cal from "@/features/calendar/api";
import type { EventInput, EventOverrideInput } from "@/features/calendar/api";

const KEY = ["calendar"] as const;

export function useOccurrences(from: string, to: string) {
  return useQuery({
    queryKey: [...KEY, "occurrences", from, to],
    queryFn: () => cal.listOccurrences(from, to),
    enabled: Boolean(from && to),
  });
}

export function useEvent(eventId: number | null) {
  return useQuery({
    queryKey: [...KEY, "event", eventId ?? 0],
    queryFn: () => cal.getEvent(eventId as number),
    enabled: eventId !== null,
  });
}

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: KEY });
}

export function useCreateEvent() {
  const invalidate = useInvalidate();
  return useMutation({ mutationFn: (input: EventInput) => cal.createEvent(input), onSuccess: invalidate });
}

export function useUpdateEvent() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<EventInput> }) =>
      cal.updateEvent(id, input),
    onSuccess: invalidate,
  });
}

export function useDeleteEvent() {
  const invalidate = useInvalidate();
  return useMutation({ mutationFn: (id: number) => cal.deleteEvent(id), onSuccess: invalidate });
}

export function useOverrides(eventId: number | null) {
  return useQuery({
    queryKey: [...KEY, "overrides", eventId ?? 0],
    queryFn: () => cal.listOverrides(eventId as number),
    enabled: eventId !== null,
  });
}

export function useUpsertOverride() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: EventOverrideInput }) =>
      cal.upsertOverride(id, input),
    onSuccess: invalidate,
  });
}

export function useDeleteOverride() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (overrideId: number) => cal.deleteOverride(overrideId),
    onSuccess: invalidate,
  });
}
