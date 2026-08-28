import { Stack, useLocalSearchParams } from "expo-router";
import { Linking, Pressable, StyleSheet, Text, View } from "react-native";

import { Card, ErrorNote, Loading, Screen, StatusBadge } from "@/components/ui";
import {
  APPLICATION_STATUSES,
  useApplication,
  useSetApplicationStatus,
  type ApplicationStatus,
} from "@/features/jobTracker/api";
import { colors, spacing } from "@/theme";

function money(app: { salary_min: number | null; salary_max: number | null; salary_currency: string }) {
  if (app.salary_min == null && app.salary_max == null) return null;
  const fmt = (n: number) => `${app.salary_currency} ${n.toLocaleString()}`;
  if (app.salary_min != null && app.salary_max != null) return `${fmt(app.salary_min)} – ${fmt(app.salary_max)}`;
  return fmt((app.salary_min ?? app.salary_max) as number);
}

export default function ApplicationDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const applicationId = Number(id);
  const query = useApplication(applicationId);
  const setStatus = useSetApplicationStatus();

  if (query.isPending) return <Loading />;
  if (query.isError || !query.data) return <ErrorNote message="Application not found." />;

  const app = query.data;
  const pay = money(app);

  return (
    <Screen>
      <Stack.Screen options={{ title: app.company.name }} />

      <Card>
        <Text style={styles.role}>{app.role}</Text>
        <Text style={styles.company}>{app.company.name}</Text>
        <StatusBadge status={app.status} />
        {app.location ? <Text style={styles.meta}>📍 {app.location}</Text> : null}
        {pay ? <Text style={styles.meta}>💰 {pay}</Text> : null}
        {app.applied_on ? <Text style={styles.meta}>🗓 Applied {app.applied_on}</Text> : null}
        {app.job_url ? (
          <Pressable onPress={() => Linking.openURL(app.job_url as string)}>
            <Text style={styles.link}>Open job posting ↗</Text>
          </Pressable>
        ) : null}
      </Card>

      <Card>
        <Text style={styles.cardTitle}>Move to</Text>
        <View style={styles.statusGrid}>
          {APPLICATION_STATUSES.filter((s) => s !== app.status).map((s) => (
            <Pressable
              key={s}
              disabled={setStatus.isPending}
              onPress={() => setStatus.mutate({ id: app.id, status: s as ApplicationStatus })}
              style={styles.statusBtn}
            >
              <Text style={styles.statusBtnText}>{s}</Text>
            </Pressable>
          ))}
        </View>
      </Card>

      <Card>
        <Text style={styles.cardTitle}>Interviews ({app.interviews.length})</Text>
        {app.interviews.length === 0 ? (
          <Text style={styles.meta}>None scheduled.</Text>
        ) : (
          app.interviews.map((iv) => (
            <View key={iv.id} style={styles.ivRow}>
              <Text style={styles.ivKind}>{iv.kind}</Text>
              <Text style={styles.meta}>
                {iv.scheduled_at ? new Date(iv.scheduled_at).toLocaleString() : "unscheduled"}
                {iv.outcome ? ` · ${iv.outcome}` : ""}
              </Text>
            </View>
          ))
        )}
      </Card>

      {app.notes ? (
        <Card>
          <Text style={styles.cardTitle}>Notes</Text>
          <Text style={styles.meta}>{app.notes}</Text>
        </Card>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  role: { color: colors.text, fontSize: 20, fontWeight: "700" },
  company: { color: colors.textDim, marginBottom: spacing(0.5) },
  meta: { color: colors.textDim, marginTop: spacing(0.5) },
  link: { color: colors.accent, marginTop: spacing(1) },
  cardTitle: { color: colors.text, fontWeight: "700", fontSize: 15, marginBottom: spacing(0.5) },
  statusGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing(1) },
  statusBtn: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 999,
    paddingHorizontal: spacing(1.5),
    paddingVertical: spacing(0.75),
  },
  statusBtnText: { color: colors.text, textTransform: "capitalize", fontSize: 13 },
  ivRow: { paddingVertical: spacing(0.75) },
  ivKind: { color: colors.text, fontWeight: "600", textTransform: "capitalize" },
});
