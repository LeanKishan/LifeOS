import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export const APPLICATION_STATUSES = [
  "wishlist",
  "applied",
  "assessment",
  "interviewing",
  "offer",
  "accepted",
  "rejected",
  "withdrawn",
] as const;

export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

export interface Company {
  id: number;
  name: string;
  website: string | null;
}

export interface Interview {
  id: number;
  kind: string;
  scheduled_at: string | null;
  outcome: string | null;
}

export interface Application {
  id: number;
  role: string;
  status: ApplicationStatus;
  location: string | null;
  job_url: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  applied_on: string | null;
  notes: string | null;
  company: Company;
  interviews: Interview[];
  created_at: string;
  updated_at: string;
}

export interface JobStats {
  total: number;
  by_status: Record<string, number>;
  active: number;
  responded: number;
  response_rate: number;
  offers: number;
  offer_rate: number;
}

const KEY = ["job-tracker"] as const;

export function useApplications(status?: ApplicationStatus) {
  return useQuery({
    queryKey: [...KEY, "applications", status ?? "all"],
    queryFn: async () => {
      const { data } = await api.get<Application[]>("/job-tracker/applications", {
        params: status ? { status } : undefined,
      });
      return data;
    },
  });
}

export function useApplication(id: number) {
  return useQuery({
    queryKey: [...KEY, "application", id],
    queryFn: async () => {
      const { data } = await api.get<Application>(`/job-tracker/applications/${id}`);
      return data;
    },
  });
}

export function useJobStats() {
  return useQuery({
    queryKey: [...KEY, "stats"],
    queryFn: async () => {
      const { data } = await api.get<JobStats>("/job-tracker/stats");
      return data;
    },
  });
}

export function useSetApplicationStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: number; status: ApplicationStatus }) => {
      const { data } = await api.patch<Application>(`/job-tracker/applications/${id}`, { status });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
