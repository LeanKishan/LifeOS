import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/features/auth/AuthContext";
import { AuthShell, Field, SubmitButton } from "@/features/auth/AuthShell";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate(location.state?.from ?? "/", { replace: true });
    } catch (err) {
      const httpStatus = (err as { response?: { status?: number } }).response?.status;
      setError(
        httpStatus === 429
          ? "Too many attempts — wait a minute and try again."
          : "Incorrect email or password.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Log in" error={error}>
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <Field
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
        />
        <SubmitButton busy={busy}>Log in</SubmitButton>
      </form>
      <p className="mt-4 text-sm text-slate-500">
        No account?{" "}
        <Link to="/register" className="text-emerald-600 hover:underline">
          Create one
        </Link>
      </p>
    </AuthShell>
  );
}
