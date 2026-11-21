import { useState } from "react";
import type { FormEvent } from "react";
import Field from "./Field";
import { editNotice, publishNotice, saveEvent, returnToLogin } from "../api/staff";
import type { EventInput, StaffEvent, StaffNotice } from "../api/staff";
import type { Zone } from "../types/api";
import { useFormErrors } from "../useFormErrors";

interface Actions { onSaved: () => void; onCancel: () => void }
export function EventEditor({ event, onSaved, onCancel }: Actions & { event?: StaffEvent }) {
  const [form, setForm] = useState<EventInput>(event ? {
    name: event.name, event_type: event.event_type, status: event.status,
    start_date: event.start_date, end_date: event.end_date,
  } : { name: "", event_type: "Wildfire", status: "Active", start_date: "", end_date: null });
  const [busy, setBusy] = useState(false);
  const errors = useFormErrors();
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    errors.clear(); setBusy(true);
    try { await saveEvent(form, event?.event_id); onSaved(); }
    catch (error) { returnToLogin(error); errors.show(error); }
    finally { setBusy(false); }
  }
  return <section className="card">
    <h2>{event ? "Edit event" : "Create event"}</h2>
    <form onSubmit={submit}>
      <fieldset disabled={busy} className="editor-fields">
        <Field label="Event name" error={errors.fields.name}><input required maxLength={100} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></Field>
        <Field label="Event type" error={errors.fields.event_type}><select value={form.event_type} onChange={e => setForm({ ...form, event_type: e.target.value as EventInput["event_type"] })}><option>Wildfire</option><option>Flood</option></select></Field>
        <Field label="Event status" error={errors.fields.status}><select value={form.status} onChange={e => setForm({ ...form, status: e.target.value as EventInput["status"] })}><option>Active</option><option>Closed</option></select></Field>
        <Field label="Start date" error={errors.fields.start_date}><input type="date" required value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} /></Field>
        <Field label="End date (optional)" error={errors.fields.end_date}><input type="date" value={form.end_date ?? ""} onChange={e => setForm({ ...form, end_date: e.target.value || null })} /></Field>
        <p className="muted">Closing an event does not cancel existing placements.</p>
        {errors.message && <p className="error" role="alert">{errors.message}</p>}
        <div className="actions"><button type="submit">{busy ? "Saving..." : "Save event"}</button><button type="button" className="secondary" onClick={onCancel}>Cancel</button></div>
      </fieldset>
    </form>
  </section>;
}

export function NoticeEditor({ event, notice, zones, onSaved, onCancel }: Actions & { event: StaffEvent; notice?: StaffNotice; zones: Zone[] }) {
  const [title, setTitle] = useState(notice?.title ?? "");
  const [message, setMessage] = useState(notice?.message ?? "");
  const [targets, setTargets] = useState<number[]>(notice?.zones.map(z => z.zone_id) ?? []);
  const [busy, setBusy] = useState(false);
  const errors = useFormErrors();
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    errors.clear(); setBusy(true);
    try {
      const data = { title, message, zone_ids: targets };
      if (notice) await editNotice(notice.notice_id, data); else await publishNotice(event.event_id, data);
      onSaved();
    } catch (error) { returnToLogin(error); errors.show(error); }
    finally { setBusy(false); }
  }
  return <section className="card">
    <h2>{notice ? "Edit notice" : "Publish notice"} — {event.name}</h2>
    {notice && <p className="muted">Originally published by {notice.publisher.name} · {new Date(notice.published_at).toLocaleString()}</p>}
    <p className="muted">Use edits for corrections. Publish a new notice for changed or lifted instructions.</p>
    <form onSubmit={submit}>
      <fieldset disabled={busy} className="editor-fields">
        <Field label="Notice title" error={errors.fields.title}><input required maxLength={150} value={title} onChange={e => setTitle(e.target.value)} /></Field>
        <Field label="Message" error={errors.fields.message}><textarea required rows={5} value={message} onChange={e => setMessage(e.target.value)} /></Field>
        <fieldset className="zone-options"><legend>Target zones</legend>
          {zones.map(zone => <label key={zone.zone_id}><input type="checkbox" checked={targets.includes(zone.zone_id)} onChange={e => setTargets(e.target.checked ? [...targets, zone.zone_id] : targets.filter(id => id !== zone.zone_id))} />{zone.zone_name}</label>)}
          {zones.length === 0 && <p>No zones are available. A notice needs at least one target zone.</p>}
        </fieldset>
        {errors.fields.zone_ids && <p className="field-error">{errors.fields.zone_ids}</p>}
        {errors.message && <p className="error" role="alert">{errors.message}</p>}
        <div className="actions"><button type="submit" disabled={zones.length === 0}>{busy ? "Saving..." : notice ? "Save notice" : "Publish notice"}</button><button type="button" className="secondary" onClick={onCancel}>Cancel</button></div>
      </fieldset>
    </form>
  </section>;
}
