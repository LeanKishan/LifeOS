import { api } from "@/lib/api";

export type ApplicationStatus =
  | "wishlist"
  | "applied"
  | "assessment"
  | "interviewing"
  | "offer"
  | "accepted"
  | "rejected"
  | "withdrawn";

export interface Company {
  id: number;
  name: string;
  website: string | null;
  notes: string | null;
  created_at: string;
}

export interface Interview {
  id: number;
  application_id: number;
  kind: string;
  scheduled_at: string | null;
  outcome: string | null;
  notes: string | null;
  created_at: string;
}

export interface Application {
  id: number;
  company: Company;
  interviews: Interview[];
  role: string;
  status: ApplicationStatus;
  source: string | null;
  location: string | null;
  job_url: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  applied_on: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobStats {
  total: number;
  by_status: Record<ApplicationStatus, number>;
  active: number;
  responded: number;
  response_rate: number;
  offers: number;
  offer_rate: number;
}

export interface ApplicationInput {
  company_name?: string;
  company_id?: number;
  role: string;
  status?: ApplicationStatus;
  source?: string | null;
  location?: string | null;
  job_url?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  applied_on?: string | null;
  notes?: string | null;
}

export interface InterviewInput {
  kind: string;
  scheduled_at?: string | null;
  outcome?: string | null;
  notes?: string | null;
}

const BASE = "/job-tracker";

export async function listApplications(
  params: { status?: ApplicationStatus; sort?: string } = {},
): Promise<Application[]> {
  const { data } = await api.get<Application[]>(`${BASE}/applications`, { params });
  return data;
}

export async function createApplication(input: ApplicationInput): Promise<Application> {
  const { data } = await api.post<Application>(`${BASE}/applications`, input);
  return data;
}

export async function updateApplication(
  id: number,
  input: Partial<ApplicationInput>,
): Promise<Application> {
  const { data } = await api.patch<Application>(`${BASE}/applications/${id}`, input);
  return data;
}

export async function deleteApplication(id: number): Promise<void> {
  await api.delete(`${BASE}/applications/${id}`);
}

export async function getJobStats(): Promise<JobStats> {
  const { data } = await api.get<JobStats>(`${BASE}/stats`);
  return data;
}

export async function addInterview(
  applicationId: number,
  input: InterviewInput,
): Promise<Interview> {
  const { data } = await api.post<Interview>(
    `${BASE}/applications/${applicationId}/interviews`,
    input,
  );
  return data;
}

export async function deleteInterview(id: number): Promise<void> {
  await api.delete(`${BASE}/interviews/${id}`);
}
