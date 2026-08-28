import { Redirect, Tabs } from "expo-router";

import { Loading } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { colors } from "@/theme";

export default function TabsLayout() {
  const { status } = useAuth();
  if (status === "loading") return <Loading />;
  if (status !== "authenticated") return <Redirect href="/login" />;

  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.surface },
        headerTintColor: colors.text,
        tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.textDim,
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Dashboard" }} />
      <Tabs.Screen name="applications" options={{ title: "Applications" }} />
    </Tabs>
  );
}
