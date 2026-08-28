import { Redirect, Stack } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Card, Field, Screen } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { colors, spacing } from "@/theme";

export default function Login() {
  const { status, signIn, signUp } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status === "authenticated") return <Redirect href="/(tabs)" />;

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await (mode === "login" ? signIn(email.trim(), password) : signUp(email.trim(), password));
    } catch {
      setError(mode === "login" ? "Wrong email or password." : "Could not create that account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: mode === "login" ? "Sign in" : "Create account" }} />
      <View style={styles.hero}>
        <Text style={styles.title}>LifeOS</Text>
        <Text style={styles.subtitle}>Your job search, on the go.</Text>
      </View>

      <Card>
        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          placeholder="you@example.com"
        />
        <Field
          label="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholder="••••••••"
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Pressable
          style={[styles.button, busy && styles.buttonDisabled]}
          disabled={busy}
          onPress={submit}
        >
          <Text style={styles.buttonText}>
            {busy ? "…" : mode === "login" ? "Sign in" : "Create account"}
          </Text>
        </Pressable>
        <Pressable onPress={() => setMode(mode === "login" ? "register" : "login")}>
          <Text style={styles.switch}>
            {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
          </Text>
        </Pressable>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: { alignItems: "center", paddingVertical: spacing(4), gap: spacing(0.5) },
  title: { color: colors.text, fontSize: 32, fontWeight: "800", letterSpacing: 1 },
  subtitle: { color: colors.textDim },
  button: {
    backgroundColor: colors.accent,
    borderRadius: 10,
    paddingVertical: spacing(1.5),
    alignItems: "center",
    marginTop: spacing(0.5),
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  switch: { color: colors.textDim, textAlign: "center", marginTop: spacing(1) },
  error: { color: colors.bad },
});
