import { useEffect, useState } from "react";
import { getZones } from "../api/auth";
import { getStaffEvents, returnToLogin } from "../api/staff";
import type { EventOverview, StaffNotice } from "../api/staff";
import type { Zone } from "../types/api";
import { EventEditor, NoticeEditor } from "../components/StaffEditors";
import { useFormErrors } from "../useFormErrors";

type Editor = { kind: "event"; event?: EventOverview } | { kind: "notice"; event: EventOverview; notice?: StaffNotice };
export default function StaffEventsPage() {
  const [data, setData] = useState<{ events: EventOverview[]; zones: Zone[]; revision: number } | null>(null);
  const [revision, setRevision] = useState(0);
  const [failedRevision, setFailedRevision] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  const [editor, setEditor] = useState<Editor | null>(null);
  const [saved, setSaved] = useState(false);
  const { message, show, clear } = useFormErrors();
  useEffect(() => {
    let cancelled = false;
    Promise.all([getStaffEvents(), getZones()]).then(([events, zones]) => {
      if (!cancelled) setData({ events, zones, revision });
    }).catch(error => {
      if (!cancelled) { returnToLogin(error); show(error); setFailedRevision(revision); }
    });
    return () => { cancelled = true; };
  }, [revision, show]);
  const ready = data?.revision === revision;
  const failed = failedRevision === revision;
  function refresh() { clear(); setRevision(r => r + 1); }
  function onSaved() { setEditor(null); setSaved(true); refresh(); }
  function open(value: Editor) { setSaved(false); setEditor(value); }
  return <section>
    <h1>Events &amp; Notices</h1>
    {saved && <p role="status">Saved successfully.</p>}
    {message && <p className="error" role="alert">{message}</p>}
    {failed && <button onClick={refresh}>Retry loading</button>}
    {!ready && !failed && <p className="muted">Loading events and zones...</p>}
    {ready && <>
      {editor?.kind === "event" && <EventEditor event={editor.event} onSaved={onSaved} onCancel={() => setEditor(null)} />}
      {editor?.kind === "notice" && <NoticeEditor event={editor.event} notice={editor.notice} zones={data.zones} onSaved={onSaved} onCancel={() => setEditor(null)} />}
      {!editor && <div className="card filters">
        <label>Show events<select value={filter} onChange={e => setFilter(e.target.value)}><option value="">All events</option><option>Active</option><option>Closed</option></select></label>
        <button onClick={() => open({ kind: "event" })}>Create event</button>
      </div>}
      {data.events.filter(event => !filter || event.status === filter).length === 0 && <p className="muted">No events match this filter.</p>}
      {data.events.filter(event => !filter || event.status === filter).map(event => <article className="card" key={event.event_id}>
        <h2>{event.name} <span className="badge">{event.status}</span></h2>
        <p className="muted">{event.event_type} · {event.start_date} to {event.end_date ?? "No end date"}</p>
        {!editor && <div className="actions"><button className="secondary" onClick={() => open({ kind: "event", event })}>Edit event: {event.name}</button><button onClick={() => open({ kind: "notice", event })}>Publish notice: {event.name}</button></div>}
        {event.notices.length === 0 && <p className="muted">No notices published for this event.</p>}
        {event.notices.map(notice => <section className="staff-notice" key={notice.notice_id}>
          <h3>{notice.title}</h3>
          <p className="muted">{notice.publisher.name} · {new Date(notice.published_at).toLocaleString()}</p>
          <p>Targets: {notice.zones.map(z => z.zone_name).join(", ")}</p>
          <p className="message">{notice.message}</p>
          {!editor && <button className="secondary" onClick={() => open({ kind: "notice", event, notice })}>Edit notice: {notice.title}</button>}
        </section>)}
      </article>)}
    </>}
  </section>;
}
