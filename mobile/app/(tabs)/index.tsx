import { Stack } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Card, ErrorNote, Loading, Screen, StatTile } from "@/components/ui";
import { useOverview } from "@/features/analytics/api";
import { useJobStats } from "@/features/jobTracker/api";
import { useAuth } from "@/lib/auth";
import { colors, spacing } from "@/theme";

export default function Dashboard() {
  const { signOut } = useAuth();
  const stats = useJobStats();
  const overview = useOverview();

  return (
    <Screen>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={styles.headerRow}>
        <Text style={styles.h1}>Dashboard</Text>
        <Pressable onPress={signOut}>
          <Text style={styles.signOut}>Sign out</Text>
        </Pressable>
      </View>

      {stats.isPending ? (
        <Loading />
      ) : stats.isError ? (
        <ErrorNote message="Could not load job stats." />
      ) : (
        <>
          <View style={styles.grid}>
            <StatTile label="Applications" value={stats.data.total} />
            <StatTile label="Active" value={stats.data.active} />
            <StatTile
              label="Response rate"
              value={`${Math.round(stats.data.response_rate * 100)}%`}
            />
            <StatTile label="Offers" value={stats.data.offers} />
          </View>

          <Card>
            <Text style={styles.cardTitle}>Pipeline</Text>
            {Object.entries(stats.data.by_status).map(([status, count]) => (
              <View key={status} style={styles.pipeRow}>
                <Text style={styles.pipeLabel}>{status}</Text>
                <Text style={styles.pipeCount}>{count}</Text>
              </View>
            ))}
          </Card>
        </>
      )}

      {overview.data ? (
        <Card>
          <Text style={styles.cardTitle}>Last 90 days</Text>
          <View style={styles.pipeRow}>
            <Text style={styles.pipeLabel}>Tasks completed</Text>
            <Text style={styles.pipeCount}>
              {overview.data.productivity.tasks_done}/{overview.data.productivity.tasks_total}
            </Text>
          </View>
          <View style={styles.pipeRow}>
            <Text style={styles.pipeLabel}>Overdue</Text>
            <Text style={styles.pipeCount}>{overview.data.productivity.overdue}</Text>
          </View>
          <View style={styles.pipeRow}>
            <Text style={styles.pipeLabel}>Flashcard reviews (7d)</Text>
            <Text style={styles.pipeCount}>{overview.data.learning.reviews_last_7d}</Text>
          </View>
        </Card>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  h1: { color: colors.text, fontSize: 26, fontWeight: "800" },
  signOut: { color: colors.textDim },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing(1.5) },
  cardTitle: { color: colors.text, fontWeight: "700", fontSize: 16, marginBottom: spacing(0.5) },
  pipeRow: { flexDirection: "row", justifyContent: "space-between", paddingVertical: spacing(0.75) },
  pipeLabel: { color: colors.textDim, textTransform: "capitalize" },
  pipeCount: { color: colors.text, fontWeight: "600" },
});
