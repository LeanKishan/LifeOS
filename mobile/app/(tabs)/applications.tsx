import { Link, Stack } from "expo-router";
import { useState } from "react";
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ErrorNote, Loading, StatusBadge } from "@/components/ui";
import {
  APPLICATION_STATUSES,
  useApplications,
  type ApplicationStatus,
} from "@/features/jobTracker/api";
import { colors, spacing } from "@/theme";

export default function Applications() {
  const [filter, setFilter] = useState<ApplicationStatus | undefined>(undefined);
  const query = useApplications(filter);

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <Stack.Screen options={{ headerShown: false }} />
      <Text style={styles.h1}>Applications</Text>

      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={["all", ...APPLICATION_STATUSES] as const}
        keyExtractor={(s) => s}
        contentContainerStyle={styles.chips}
        renderItem={({ item }) => {
          const active = item === "all" ? filter === undefined : filter === item;
          return (
            <Pressable
              onPress={() => setFilter(item === "all" ? undefined : (item as ApplicationStatus))}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{item}</Text>
            </Pressable>
          );
        }}
      />

      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorNote message="Could not load applications." />
      ) : (
        <FlatList
          data={query.data}
          keyExtractor={(a) => String(a.id)}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={query.isRefetching}
              onRefresh={query.refetch}
              tintColor={colors.textDim}
            />
          }
          ListEmptyComponent={<Text style={styles.empty}>No applications yet.</Text>}
          renderItem={({ item }) => (
            <Link href={`/application/${item.id}`} asChild>
              <Pressable style={styles.row}>
                <View style={styles.rowMain}>
                  <Text style={styles.role}>{item.role}</Text>
                  <Text style={styles.company}>{item.company.name}</Text>
                </View>
                <StatusBadge status={item.status} />
              </Pressable>
            </Link>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  h1: { color: colors.text, fontSize: 26, fontWeight: "800", padding: spacing(2) },
  chips: { paddingHorizontal: spacing(2), gap: spacing(1), paddingBottom: spacing(1) },
  chip: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing(1.5),
    paddingVertical: spacing(0.75),
  },
  chipActive: { backgroundColor: colors.accent, borderColor: colors.accent },
  chipText: { color: colors.textDim, textTransform: "capitalize", fontSize: 13 },
  chipTextActive: { color: "#fff", fontWeight: "600" },
  list: { padding: spacing(2), gap: spacing(1) },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: spacing(1.75),
  },
  rowMain: { flex: 1, gap: 2 },
  role: { color: colors.text, fontWeight: "600", fontSize: 15 },
  company: { color: colors.textDim, fontSize: 13 },
  empty: { color: colors.textDim, textAlign: "center", padding: spacing(4) },
});
