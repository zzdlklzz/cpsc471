import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "../router";
import CredentialFields from "../components/CredentialFields";
import { useAuth } from "../context/authContext";
import { ROUTES } from "../routes";
import type { Credentials, CurrentUser } from "../types/api";
import { useFormErrors } from "../useFormErrors";

/** Staff go to the staff navigation, households to My Household. */
function homeFor(user: CurrentUser): string {
  return user.role === "staff" ? ROUTES.staffHome : ROUTES.household;
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<Credentials>({ login_email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const errors = useFormErrors();

  if (user) return <Navigate to={homeFor(user)} replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    errors.clear();
    try {
      navigate(homeFor(await login(form)));
    } catch (err) {
      errors.show(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card narrow">
      <h1>Log in</h1>
      <form onSubmit={handleSubmit}>
        <CredentialFields value={form} errors={errors.fields} onChange={setForm} />
        {errors.message && <p className="error">{errors.message}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Logging in..." : "Log in"}
        </button>
      </form>
      <p className="muted">
        New household? <Link to={ROUTES.signup}>Create an account</Link>
      </p>
    </section>
  );
}
