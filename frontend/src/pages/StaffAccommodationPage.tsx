import { useEffect, useState } from "react";
import { api } from "../api/client";
import { returnToLogin } from "../api/staff";

type Person = { member_id: number; first_name: string; last_name: string; phone_number: string | null; email?: string };
type Placement = { registration_id: number; placement_no: number; status: string; created_at: string; arrival_time: string | null; departure_time: string | null; shelter: { shelter_id: number; name: string; address: string } };
type Registration = { registration_id: number; status: string; household: { household_id: number }; event: { name: string }; contact: Person | null; participants: Person[]; participant_count: number; current_placement: Placement | null; placements?: Placement[] };
type ShelterResult = { shelter: Placement["shelter"]; placements: (Placement & Registration)[] };

export default function StaffAccommodationPage() {
  const [event, setEvent] = useState("");
  const [registration, setRegistration] = useState("");
  const [query, setQuery] = useState("");
  const [selection, setSelection] = useState<{ kind: "registration" | "shelter"; id: number } | null>(null);
  const [view, setView] = useState("reservations");
  const [rows, setRows] = useState<Registration[]>([]);
  const [detail, setDetail] = useState<Registration | null>(null);
  const [shelter, setShelter] = useState<ShelterResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    const path = selection?.kind === "registration" ? `/staff/registrations/${selection.id}` : selection?.kind === "shelter" ? `/staff/shelters/${selection.id}/placements?view=${view}${new URLSearchParams(query).get("event_id") ? `&event_id=${new URLSearchParams(query).get("event_id")}` : ""}` : `/staff/registrations?${query}`;
    api<{ registrations: Registration[] } | Registration | ShelterResult>(path).then(data => {
      if (!active) return;
      if ("registrations" in data) setRows(data.registrations);
      else if ("shelter" in data) setShelter(data);
      else setDetail(data);
    }).catch(err => { if (active) { returnToLogin(err); setError(err instanceof Error ? err.message : "Unable to load accommodation."); } }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [selection, view, query, retry]);
  function reset() { setLoading(true); setError(""); setDetail(null); setShelter(null); }
  function open(kind: "registration" | "shelter", id: number) { reset(); setSelection({ kind, id }); setView("reservations"); }
  function placement(p: Placement) { return <li key={`${p.registration_id}-${p.placement_no}`}>Placement {p.placement_no}: {p.status} — <button type="button" onClick={() => open("shelter", p.shelter.shelter_id)}>{p.shelter.name}</button><p>{p.shelter.address} · Created: {p.created_at} · Arrival: {p.arrival_time ?? "Not recorded"} · Departure: {p.departure_time ?? "Not recorded"}</p></li>; }
  function people(r: Registration) { return <><p>Contact: {r.contact ? `${r.contact.first_name} ${r.contact.last_name} · ${r.contact.phone_number ?? "No phone"} · ${r.contact.email ?? "No email"}` : "No contact recorded"}</p><p>Participants: {r.participant_count}</p><ul>{r.participants.map(p => <li key={p.member_id}>{p.first_name} {p.last_name} · {p.phone_number ?? "No phone"}</li>)}</ul></>; }
  return <section className="accommodation"><h1>Accommodation</h1><p>Read-only registrations and placement history.</p>
    <form className="card filters" onSubmit={e => { e.preventDefault(); reset(); setSelection(null); setQuery(new URLSearchParams({ ...(event ? { event_id: event } : {}), ...(registration ? { registration_id: registration } : {}) }).toString()); setRetry(n => n + 1); }}>
      <label>Event ID <input type="number" min="1" step="1" value={event} onChange={e => setEvent(e.target.value)} /></label>
      <label>Registration ID <input type="number" min="1" step="1" value={registration} onChange={e => setRegistration(e.target.value)} /></label><button>Find registrations</button>
    </form>
    {selection && <button className="secondary" onClick={() => { reset(); setSelection(null); }}>Back to registrations</button>}
    {selection?.kind === "shelter" && <label className="field placement-view">Placement view <select value={view} onChange={e => { reset(); setView(e.target.value); }}><option value="reservations">Reservations</option><option value="occupants">Occupants</option><option value="history">History</option></select></label>}
    {loading ? <p role="status">Loading accommodation…</p> : error ? <div role="alert"><p>{error}</p><button onClick={() => { reset(); setRetry(n => n + 1); }}>Retry loading</button></div> : <>
      {!selection && (rows.length ? <ul>{rows.map(r => <li key={r.registration_id}><button onClick={() => open("registration", r.registration_id)}>Registration {r.registration_id}</button> — Household {r.household.household_id} · {r.event.name} · {r.status} · {r.participant_count} participants · {r.current_placement ? `${r.current_placement.shelter.name}: ${r.current_placement.status}` : "No current placement"}</li>)}</ul> : <p>No registrations found.</p>)}
      {detail && <><h2>Registration {detail.registration_id}</h2><p>Household {detail.household.household_id} · {detail.event.name} · {detail.status}</p>{people(detail)}<h3>Current placement</h3>{detail.current_placement ? <ul>{placement(detail.current_placement)}</ul> : <p>No current placement.</p>}<h3>Placement history</h3>{detail.placements?.length ? <ul>{detail.placements.map(placement)}</ul> : <p>No placement history.</p>}</>}
      {shelter && <><h2>{shelter.shelter.name}</h2><p>{shelter.shelter.address}</p>{shelter.placements.length ? <ul>{shelter.placements.map(p => <li key={`${p.registration_id}-${p.placement_no}`}><button onClick={() => open("registration", p.registration_id)}>Registration {p.registration_id}</button> · Placement {p.placement_no} · {p.status} · {p.event.name}{people(p)}<p>Arrival: {p.arrival_time ?? "Not recorded"} · Departure: {p.departure_time ?? "Not recorded"}</p></li>)}</ul> : <p>No placements in this view.</p>}</>}
    </>}
  </section>;
}
