import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, toApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { AuthResponse } from "../lib/types";
import { Alert, Field } from "../components/ui";

export function RegisterPage() {
  const { setSession } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof form>(k: K, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setBusy(true);
    try {
      const { data } = await api.post<AuthResponse>("/api/auth/register", form);
      await setSession(data);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const apiErr = toApiError(err);
      if (apiErr.fieldErrors) setFieldErrors(apiErr.fieldErrors);
      if (apiErr.status === 409) setError("An account with this email already exists.");
      else if (!apiErr.fieldErrors) setError(apiErr.message || "Registration failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h1 style={{ fontSize: "1.4rem" }}>Inspector Registration</h1>
        <p className="small muted">
          New accounts are created with the <strong>Inspector</strong> role. Administrator access is
          granted separately.
        </p>

        {error && <Alert kind="error">{error}</Alert>}

        <form onSubmit={onSubmit} noValidate>
          <Field label="Full name / username" htmlFor="username" required error={fieldErrors.username}>
            <input
              id="username"
              value={form.username}
              onChange={(e) => set("username", e.target.value)}
              required
            />
          </Field>
          <Field label="Official email" htmlFor="email" required error={fieldErrors.email}>
            <input
              id="email"
              type="email"
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
              required
            />
          </Field>
          <Field
            label="Password"
            htmlFor="password"
            required
            error={fieldErrors.password}
            hint="At least 8 characters."
          >
            <input
              id="password"
              type="password"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
              required
            />
          </Field>
          <button className="btn" type="submit" disabled={busy}>
            {busy ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="small" style={{ marginTop: 16 }}>
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
