import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/features/auth/AuthContext";
import { AuthShell, Field, SubmitButton } from "@/features/auth/AuthShell";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register(email, password, fullName);
      navigate("/", { replace: true });
    } catch {
      setError(
        "Could not create the account. The email may already be in use, " +
          "or the password is shorter than 8 characters.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Create your account" error={error}>
      <form onSubmit={onSubmit} className="space-y-4">
        <Field
          label="Full name"
          type="text"
          value={fullName}
          onChange={setFullName}
          autoComplete="name"
          required={false}
        />
        <Field label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <Field
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
        />
        <SubmitButton busy={busy}>Create account</SubmitButton>
      </form>
      <p className="mt-4 text-sm text-slate-500">
        Already have an account?{" "}
        <Link to="/login" className="text-emerald-600 hover:underline">
          Log in
        </Link>
      </p>
    </AuthShell>
  );
}
