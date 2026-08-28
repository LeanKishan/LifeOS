import { type ReactNode } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  type TextInputProps,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors, spacing, STATUS_COLORS } from "@/theme";

export function Screen({ children, scroll = true }: { children: ReactNode; scroll?: boolean }) {
  const Body = scroll ? ScrollView : View;
  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <Body
        style={styles.body}
        contentContainerStyle={scroll ? styles.bodyContent : undefined}
      >
        {children}
      </Body>
    </SafeAreaView>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: object }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={styles.tile}>
      <Text style={styles.tileValue}>{value}</Text>
      <Text style={styles.tileLabel}>{label}</Text>
    </View>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <View style={[styles.badge, { backgroundColor: STATUS_COLORS[status] ?? colors.textDim }]}>
      <Text style={styles.badgeText}>{status}</Text>
    </View>
  );
}

export function Field(props: TextInputProps & { label: string }) {
  const { label, style, ...rest } = props;
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.textDim}
        style={[styles.input, style]}
        {...rest}
      />
    </View>
  );
}

export function Loading() {
  return (
    <View style={styles.center}>
      <ActivityIndicator color={colors.accent} />
    </View>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <View style={styles.center}>
      <Text style={{ color: colors.bad }}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  body: { flex: 1, backgroundColor: colors.bg },
  bodyContent: { padding: spacing(2), gap: spacing(1.5) },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 14,
    padding: spacing(2),
    gap: spacing(1),
  },
  tile: {
    flexGrow: 1,
    flexBasis: "45%",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 14,
    padding: spacing(2),
  },
  tileValue: { color: colors.text, fontSize: 24, fontWeight: "700" },
  tileLabel: { color: colors.textDim, marginTop: spacing(0.5) },
  badge: { alignSelf: "flex-start", borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3 },
  badgeText: { color: "#fff", fontSize: 12, fontWeight: "600", textTransform: "capitalize" },
  field: { gap: spacing(0.5) },
  fieldLabel: { color: colors.textDim, fontSize: 13 },
  input: {
    backgroundColor: colors.bg,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: spacing(1.5),
    paddingVertical: spacing(1.25),
    color: colors.text,
  },
  center: { padding: spacing(3), alignItems: "center", justifyContent: "center" },
});
