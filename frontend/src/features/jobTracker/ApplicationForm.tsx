import { useState, type FormEvent, type ReactNode } from "react";

import type { ApplicationInput, ApplicationStatus } from "@/features/jobTracker/api";
import { STATUS_META, STATUS_ORDER } from "@/features/jobTracker/statusMeta";

const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none " +
  "focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900";

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-500">{label}</span>
      {children}
    </label>
  );
}

export function ApplicationForm({
  initial,
  showCompany,
  submitLabel,
  pending,
  onSubmit,
}: {
  initial?: Partial<ApplicationInput>;
  showCompany: boolean;
  submitLabel: string;
  pending: boolean;
  onSubmit: (input: ApplicationInput) => void;
}) {
  const [companyName, setCompanyName] = useState(initial?.company_name ?? "");
  const [role, setRole] = useState(initial?.role ?? "");
  const [status, setStatus] = useState<ApplicationStatus>(initial?.status ?? "applied");
  const [source, setSource] = useState(initial?.source ?? "");
  const [location, setLocation] = useState(initial?.location ?? "");
  const [jobUrl, setJobUrl] = useState(initial?.job_url ?? "");
  const [salaryMin, setSalaryMin] = useState(initial?.salary_min?.toString() ?? "");
  const [salaryMax, setSalaryMax] = useState(initial?.salary_max?.toString() ?? "");
  const [appliedOn, setAppliedOn] = useState(initial?.applied_on ?? "");
  const [notes, setNotes] = useState(initial?.notes ?? "");

  function submit(event: FormEvent): void {
    event.preventDefault();
    const payload: ApplicationInput = {
      role: role.trim(),
      status,
      source: source.trim() || null,
      location: location.trim() || null,
      job_url: jobUrl.trim() || null,
      salary_min: salaryMin ? Number(salaryMin) : null,
      salary_max: salaryMax ? Number(salaryMax) : null,
      applied_on: appliedOn || null,
      notes: notes.trim() || null,
    };
    if (showCompany) payload.company_name = companyName.trim();
    onSubmit(payload);
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      {showCompany && (
        <Row label="Company">
          <input
            className={inputClass}
            value={companyName}
            required
            onChange={(event) => setCompanyName(event.target.value)}
          />
        </Row>
      )}
      <Row label="Role">
        <input
          className={inputClass}
          value={role}
          required
          onChange={(event) => setRole(event.target.value)}
        />
      </Row>
      <Row label="Status">
        <select
          className={inputClass}
          value={status}
          onChange={(event) => setStatus(event.target.value as ApplicationStatus)}
        >
          {STATUS_ORDER.map((value) => (
            <option key={value} value={value}>
              {STATUS_META[value].label}
            </option>
          ))}
        </select>
      </Row>
      <div className="grid grid-cols-2 gap-3">
        <Row label="Source">
          <input
            className={inputClass}
            value={source}
            placeholder="LinkedIn, referral…"
            onChange={(event) => setSource(event.target.value)}
          />
        </Row>
        <Row label="Location">
          <input
            className={inputClass}
            value={location}
            onChange={(event) => setLocation(event.target.value)}
          />
        </Row>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Row label="Salary min">
          <input
            className={inputClass}
            type="number"
            min={0}
            value={salaryMin}
            onChange={(event) => setSalaryMin(event.target.value)}
          />
        </Row>
        <Row label="Salary max">
          <input
            className={inputClass}
            type="number"
            min={0}
            value={salaryMax}
            onChange={(event) => setSalaryMax(event.target.value)}
          />
        </Row>
      </div>
      <Row label="Applied on">
        <input
          className={inputClass}
          type="date"
          value={appliedOn}
          onChange={(event) => setAppliedOn(event.target.value)}
        />
      </Row>
      <Row label="Job URL">
        <input
          className={inputClass}
          value={jobUrl}
          onChange={(event) => setJobUrl(event.target.value)}
        />
      </Row>
      <Row label="Notes">
        <textarea
          className={inputClass}
          rows={3}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />
      </Row>
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {pending ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
