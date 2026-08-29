import { useMemo, useState } from "react";

import { Button, Card, CardHeader, Field, PageHeader, Select } from "@/components/ui";
import { useAuth } from "@/features/auth/AuthContext";

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
    <div className="max-w-xl">
      <PageHeader title="Settings" subtitle={user?.email} />

      <Card>
        <CardHeader title="Timezone" />
        <p className="text-sm text-muted">
          Analytics day, week and month boundaries — and the assistant's idea of
          "today" — use this. Everything is still stored in UTC.
        </p>
        <div className="mt-4 space-y-3">
          <Field>
            <Select value={tz} onChange={(e) => setTz(e.target.value)}>
              {options.map((zone) => (
                <option key={zone} value={zone}>
                  {zone}
                  {zone === detected ? "  (detected)" : ""}
                </option>
              ))}
            </Select>
          </Field>
          <p className="text-xs text-faint">
            Now, there: <span className="tabular-nums text-muted">{localTime}</span>
          </p>
          <div className="flex items-center gap-3 pt-1">
            <Button
              variant="primary"
              icon="check"
              disabled={!dirty}
              loading={state === "saving"}
              onClick={() => void save()}
            >
              Save
            </Button>
            {state === "saved" && <span className="text-sm text-brand-hi">Saved</span>}
            {state === "error" && (
              <span className="text-sm text-rose-400">Could not save — try again.</span>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
