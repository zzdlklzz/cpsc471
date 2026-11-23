import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "../router";
import CredentialFields from "../components/CredentialFields";
import { useAuth } from "../context/authContext";
import { ROUTES } from "../routes";
import type { Credentials, CurrentUser, Role } from "../types/api";
import { useFormErrors } from "../useFormErrors";

/** Staff go to the staff navigation, households to My Household. */
function homeFor(user: CurrentUser): string {
  return user.role === "staff" ? ROUTES.staffHome : ROUTES.household;
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<Credentials>({ login_email: "", password: "" });
  const [role, setRole] = useState<Role>("household");
  const [busy, setBusy] = useState(false);
  const errors = useFormErrors();

  if (user) return <Navigate to={homeFor(user)} replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    errors.clear();
    try {
      navigate(homeFor(await login(form, role)));
    } catch (err) {
      errors.show(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card narrow">
      <h1>Log in</h1>
      <div className="login-tabs" role="tablist" aria-label="Login type">
        {(["household", "staff"] as const).map((option) => (
          <button key={option} type="button" role="tab" id={`${option}-tab`}
            aria-selected={role === option} aria-controls="login-panel"
            disabled={busy} tabIndex={role === option ? 0 : -1}
            onKeyDown={(e) => {
              if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
              e.preventDefault();
              const next = e.key === "Home" ? "household" : e.key === "End" ? "staff"
                : option === "household" ? "staff" : "household";
              const button = e.currentTarget.parentElement?.querySelector<HTMLButtonElement>(`#${next}-tab`);
              button?.focus();
              button?.click();
            }}
            onClick={() => {
              setRole(option);
              setForm({ login_email: "", password: "" });
              errors.clear();
            }}>
            {option === "household" ? "Household Login" : "Staff Login"}
          </button>
        ))}
      </div>
      <div id="login-panel" role="tabpanel" aria-labelledby={`${role}-tab`}>
      <form onSubmit={handleSubmit}>
        <CredentialFields value={form} errors={errors.fields} onChange={setForm} />
        {errors.message && <p className="error">{errors.message}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Logging in..." : "Log in"}
        </button>
      </form>
      {role === "household" && <p className="muted">
        New household? <Link to={ROUTES.signup}>Create an account</Link>
      </p>}
      </div>
    </section>
  );
}
