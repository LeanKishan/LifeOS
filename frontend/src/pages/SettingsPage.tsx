import { useMemo, useState } from "react";

import { useAuth } from "@/features/auth/AuthContext";

// A curated set of IANA zones; the browser's own zone is prepended if missing.
const ZONES = [
  "UTC",
  "America/Los_Angeles",
  "America/Denver",
  "America/Chicago",
  "America/New_York",
  "America/Sao_Paulo",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Athens",
  "Africa/Johannesburg",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Asia/Shanghai",
  "Asia/Tokyo",
  "Australia/Sydney",
  "Pacific/Auckland",
];

export default function SettingsPage() {
  const { user, updateProfile } = useAuth();
  const detected = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
      return "";
    }
  }, []);

  const options = useMemo(() => {
    const set = new Set(ZONES);
    if (user?.timezone) set.add(user.timezone);
    if (detected) set.add(detected);
    return [...set].sort();
  }, [user?.timezone, detected]);

  const [tz, setTz] = useState(user?.timezone ?? "UTC");
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  async function save(): Promise<void> {
    setState("saving");
    try {
      await updateProfile({ timezone: tz });
      setState("saved");
      window.setTimeout(() => setState("idle"), 2000);
    } catch {
      setState("error");
    }
  }

  const dirty = tz !== (user?.timezone ?? "UTC");
  const localTime = useMemo(() => {
    try {
      return new Intl.DateTimeFormat([], {
        timeZone: tz,
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date());
    } catch {
      return "—";
    }
  }, [tz]);

  return (
    <div className="max-w-lg">
      <h2 className="mb-6 text-xl font-semibold">Settings</h2>

      <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <label htmlFor="tz" className="block text-sm font-medium">
          Timezone
        </label>
        <p className="mt-1 text-xs text-slate-500">
          Analytics day, week and month boundaries — and the assistant’s idea of
          “today” — use this. Everything is still stored in UTC.
        </p>
        <select
          id="tz"
          value={tz}
          onChange={(e) => setTz(e.target.value)}
          className="mt-3 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
        >
          {options.map((zone) => (
            <option key={zone} value={zone}>
              {zone}
              {zone === detected ? " (detected)" : ""}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-slate-400">Now, there: {localTime}</p>

        <div className="mt-4 flex items-center gap-3">
          <button
            type="button"
            onClick={() => void save()}
            disabled={!dirty || state === "saving"}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {state === "saving" ? "Saving…" : "Save"}
          </button>
          {state === "saved" && <span className="text-sm text-emerald-600">Saved</span>}
          {state === "error" && (
            <span className="text-sm text-rose-600">Could not save — try again.</span>
          )}
        </div>
      </div>
    </div>
  );
}
