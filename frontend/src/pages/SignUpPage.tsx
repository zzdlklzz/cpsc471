import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "../router";
import { getZones } from "../api/auth";
import CredentialFields from "../components/CredentialFields";
import HouseholdFields from "../components/HouseholdFields";
import MemberFields from "../components/MemberFields";
import { useAuth } from "../context/authContext";
import { ROUTES } from "../routes";
import type { Credentials, HouseholdInput, MemberInput, Zone } from "../types/api";
import { useFormErrors } from "../useFormErrors";

/** Creates the household, the first member and the login in one step. Households only. */
export default function SignUpPage() {
  const { user, signup } = useAuth();
  const navigate = useNavigate();
  const [zones, setZones] = useState<Zone[]>([]);
  const [household, setHousehold] = useState<HouseholdInput>({ street: "", city: "", province: "Alberta", postal_code: "", zone_id: 0 });
  const [member, setMember] = useState<MemberInput>({ first_name: "", last_name: "", date_of_birth: "", phone_number: "" });
  const [creds, setCreds] = useState<Credentials>({ login_email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const errors = useFormErrors();
  const { show: showError } = errors;

  useEffect(() => {
    getZones().then(setZones).catch(showError);
  }, [showError]);

  if (user) return <Navigate to={ROUTES.household} replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    errors.clear();
    try {
      await signup({ ...household, ...member, ...creds });
      navigate(ROUTES.household);
    } catch (err) {
      errors.show(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h1>Create a household account</h1>
      <form onSubmit={handleSubmit}>
        <h2>Your details</h2>
        <MemberFields value={member} errors={errors.fields} onChange={setMember} />
        <h2>Login</h2>
        <CredentialFields value={creds} errors={errors.fields} onChange={setCreds} newPassword />
        <h2>Household address</h2>
        <HouseholdFields value={household} zones={zones} errors={errors.fields} onChange={setHousehold} />
        {errors.message && <p className="error">{errors.message}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Creating..." : "Create account"}
        </button>
      </form>
      <p className="muted">
        Already have an account? <Link to={ROUTES.login}>Log in</Link>
      </p>
    </section>
  );
}
