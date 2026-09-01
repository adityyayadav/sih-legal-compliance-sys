import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { api, toApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { AuthResponse } from "../lib/types";
import { Alert, Field } from "../components/ui";

export function LoginPage() {
  const { setSession, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const from = location.state?.from ?? "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const { data } = await api.post<AuthResponse>("/api/auth/login", { email, password });
      await setSession(data);
      navigate(from, { replace: true });
    } catch (err) {
      const apiErr = toApiError(err);
      setError(
        apiErr.status === 401 ? "Invalid email or password." : apiErr.message || "Login failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h1 style={{ fontSize: "1.4rem" }}>Officer Login</h1>
        <p className="small muted">Access is restricted to registered inspectors and administrators.</p>

        {error && <Alert kind="error">{error}</Alert>}

        <form onSubmit={onSubmit} noValidate>
          <Field label="Email" htmlFor="email" required>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </Field>
          <Field label="Password" htmlFor="password" required>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Field>
          <button className="btn" type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="small" style={{ marginTop: 16 }}>
          New inspector? <Link to="/register">Register here</Link>
        </p>
        <p className="small muted">
          Demo: <code>admin@packsure.test / Admin@12345</code> ·{" "}
          <code>inspector@packsure.test / Inspector@123</code>
        </p>
      </div>
    </div>
  );
}
