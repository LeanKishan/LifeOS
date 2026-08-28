import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as jt from "@/features/jobTracker/api";
import type { ApplicationInput, ApplicationStatus, InterviewInput } from "@/features/jobTracker/api";

const KEY = ["job-tracker"] as const;

export function useApplications(params: { status?: ApplicationStatus; sort?: string } = {}) {
  return useQuery({
    queryKey: [...KEY, "applications", params],
    queryFn: () => jt.listApplications(params),
  });
}

export function useJobStats() {
  return useQuery({ queryKey: [...KEY, "stats"], queryFn: jt.getJobStats });
}

function useInvalidateAll() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: KEY });
}

export function useCreateApplication() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (input: ApplicationInput) => jt.createApplication(input),
    onSuccess: invalidate,
  });
}

export function useUpdateApplication() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<ApplicationInput> }) =>
      jt.updateApplication(id, input),
    onSuccess: invalidate,
  });
}

export function useDeleteApplication() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (id: number) => jt.deleteApplication(id),
    onSuccess: invalidate,
  });
}

export function useAddInterview() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: ({ applicationId, input }: { applicationId: number; input: InterviewInput }) =>
      jt.addInterview(applicationId, input),
    onSuccess: invalidate,
  });
}

export function useDeleteInterview() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (id: number) => jt.deleteInterview(id),
    onSuccess: invalidate,
  });
}
