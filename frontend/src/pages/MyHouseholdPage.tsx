import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { getZones } from "../api/auth";
import * as householdApi from "../api/household";
import CredentialFields from "../components/CredentialFields";
import HouseholdFields from "../components/HouseholdFields";
import MemberFields from "../components/MemberFields";
import { useAuth } from "../context/authContext";
import type { Credentials, Household, HouseholdInput, Member, MemberInput, Zone } from "../types/api";
import { useFormErrors } from "../useFormErrors";

// Which form panel is open. Only one at a time.
type Panel =
  | { kind: "none" }
  | { kind: "editHousehold" }
  | { kind: "addMember" }
  | { kind: "editMember"; member: Member }
  | { kind: "enableAccount"; member: Member };

const EMPTY_MEMBER: MemberInput = { first_name: "", last_name: "", date_of_birth: "", phone_number: "" };

export default function MyHouseholdPage() {
  const { user } = useAuth();
  const [household, setHousehold] = useState<Household | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [panel, setPanel] = useState<Panel>({ kind: "none" });
  const [householdForm, setHouseholdForm] = useState<HouseholdInput>({ street: "", city: "", province: "", postal_code: "", zone_id: 0 });
  const [memberForm, setMemberForm] = useState<MemberInput>(EMPTY_MEMBER);
  const [credsForm, setCredsForm] = useState<Credentials>({ login_email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const pageErrors = useFormErrors();
  const { show: showPageError } = pageErrors;
  const formErrors = useFormErrors();

  useEffect(() => {
    householdApi.getHousehold().then(setHousehold).catch(showPageError);
    getZones().then(setZones).catch(showPageError);
  }, [showPageError]);

  function open(next: Panel) {
    formErrors.clear();
    pageErrors.clear();
    if (next.kind === "editHousehold" && household) {
      setHouseholdForm({ street: household.street, city: household.city, province: household.province, postal_code: household.postal_code, zone_id: household.zone.zone_id });
    }
    if (next.kind === "addMember") setMemberForm(EMPTY_MEMBER);
    if (next.kind === "editMember") {
      const m = next.member;
      setMemberForm({ first_name: m.first_name, last_name: m.last_name, date_of_birth: m.date_of_birth, phone_number: m.phone_number ?? "" });
    }
    if (next.kind === "enableAccount") setCredsForm({ login_email: "", password: "" });
    setPanel(next);
  }

  /** Runs one save action. Every action returns the updated household. */
  async function save(action: () => Promise<Household>) {
    setBusy(true);
    formErrors.clear();
    try {
      setHousehold(await action());
      setPanel({ kind: "none" });
    } catch (err) {
      formErrors.show(err);
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (panel.kind === "editHousehold") void save(() => householdApi.updateHousehold(householdForm));
    if (panel.kind === "addMember") void save(() => householdApi.addMember(memberForm));
    if (panel.kind === "editMember") void save(() => householdApi.updateMember(panel.member.member_id, memberForm));
    if (panel.kind === "enableAccount") void save(() => householdApi.enableMemberAccount(panel.member.member_id, credsForm));
  }

  async function handleRemove(member: Member) {
    if (!window.confirm(`Remove ${member.first_name} ${member.last_name} from the household?`)) return;
    pageErrors.clear();
    try {
      setHousehold(await householdApi.removeMember(member.member_id));
      setPanel({ kind: "none" });
    } catch (err) {
      pageErrors.show(err);
    }
  }

  if (!household) {
    return <p className={pageErrors.message ? "error" : "muted"}>{pageErrors.message || "Loading your household..."}</p>;
  }

  const panelTitle =
    panel.kind === "editHousehold" ? "Edit household"
    : panel.kind === "addMember" ? "Add member"
    : panel.kind === "editMember" ? `Edit ${panel.member.first_name} ${panel.member.last_name}`
    : panel.kind === "enableAccount" ? `Give ${panel.member.first_name} ${panel.member.last_name} a login`
    : "";

  return (
    <section>
      <h1>My Household</h1>
      {pageErrors.message && <p className="error">{pageErrors.message}</p>}

      <div className="card">
        <div className="card-head">
          <h2>Address</h2>
          <button type="button" className="secondary" onClick={() => open({ kind: "editHousehold" })}>
            Edit household
          </button>
        </div>
        <p>
          {household.street}, {household.city}, {household.province} {household.postal_code}
        </p>
        <p>
          <strong>Home zone:</strong> {household.zone.zone_name}
        </p>
      </div>

      <div className="card">
        <div className="card-head">
          <h2>Members</h2>
          <button type="button" className="secondary" onClick={() => open({ kind: "addMember" })}>
            Add member
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Date of birth</th>
              <th>Phone</th>
              <th>Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {household.members.map((m) => (
              <tr key={m.member_id}>
                <td>
                  {m.first_name} {m.last_name}
                  {m.member_id === user?.member_id && <span className="badge">You</span>}
                </td>
                <td>{m.date_of_birth}</td>
                <td>{m.phone_number ?? "-"}</td>
                <td>{m.is_account_holder ? <span className="badge ok">Account holder</span> : "No login"}</td>
                <td className="actions">
                  <button type="button" className="link" onClick={() => open({ kind: "editMember", member: m })}>
                    Edit
                  </button>
                  {!m.is_account_holder && (
                    <button type="button" className="link" onClick={() => open({ kind: "enableAccount", member: m })}>
                      Enable login
                    </button>
                  )}
                  {m.member_id !== user?.member_id && (
                    <button type="button" className="link danger" onClick={() => handleRemove(m)}>
                      Remove
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {panel.kind !== "none" && (
        <div className="card">
          <h2>{panelTitle}</h2>
          <form onSubmit={handleSubmit}>
            {panel.kind === "editHousehold" && (
              <HouseholdFields value={householdForm} zones={zones} errors={formErrors.fields} onChange={setHouseholdForm} />
            )}
            {(panel.kind === "addMember" || panel.kind === "editMember") && (
              <MemberFields value={memberForm} errors={formErrors.fields} onChange={setMemberForm} />
            )}
            {panel.kind === "enableAccount" && (
              <CredentialFields value={credsForm} errors={formErrors.fields} onChange={setCredsForm} newPassword />
            )}
            {formErrors.message && <p className="error">{formErrors.message}</p>}
            <div className="actions">
              <button type="submit" disabled={busy}>
                {busy ? "Saving..." : "Save"}
              </button>
              <button type="button" className="secondary" onClick={() => setPanel({ kind: "none" })}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
