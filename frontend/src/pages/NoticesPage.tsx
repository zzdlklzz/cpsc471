import { useEffect, useState } from "react";
import { getZones } from "../api/auth";
import { getEvents, getNotices } from "../api/notices";
import type { NoticeFilters } from "../api/notices";
import { Link } from "../router";
import { ROUTES } from "../routes";
import type { EventSummary, Notice, Zone } from "../types/api";
import { useFormErrors } from "../useFormErrors";

/** The notices that belong to one set of filters. */
interface Loaded {
  key: string;
  rows: Notice[];
}

export default function NoticesPage() {
  const [filters, setFilters] = useState<NoticeFilters>({ scope: "mine", eventId: "", zoneId: "" });
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const errors = useFormErrors();
  const { show: showError } = errors;

  useEffect(() => {
    getEvents().then(setEvents).catch(showError);
    getZones().then(setZones).catch(showError);
  }, [showError]);

  const { scope, eventId, zoneId } = filters;
  const key = `${scope}|${eventId}|${zoneId}`;

  useEffect(() => {
    let cancelled = false; // ignore a slow answer if the filters changed again
    getNotices({ scope, eventId, zoneId })
      .then((rows) => {
        if (!cancelled) setLoaded({ key: `${scope}|${eventId}|${zoneId}`, rows });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          showError(err);
          setLoaded({ key: `${scope}|${eventId}|${zoneId}`, rows: [] });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [scope, eventId, zoneId, showError]);

  // Show the list only when it belongs to the filters on screen.
  const notices = loaded && loaded.key === key ? loaded.rows : null;

  return (
    <section>
      <h1>Notices</h1>
      <div className="card filters">
        <label>
          Show
          <select value={scope} onChange={(e) => setFilters({ ...filters, scope: e.target.value as "mine" | "all", zoneId: "" })}>
            <option value="mine">Notices for my zone</option>
            <option value="all">All notices</option>
          </select>
        </label>
        <label>
          Event
          <select value={eventId} onChange={(e) => setFilters({ ...filters, eventId: e.target.value })}>
            <option value="">All events</option>
            {events.map((ev) => (
              <option key={ev.event_id} value={ev.event_id}>
                {ev.name} ({ev.status})
              </option>
            ))}
          </select>
        </label>
        <label>
          Zone
          <select value={zoneId} onChange={(e) => setFilters({ ...filters, zoneId: e.target.value, scope: e.target.value ? "all" : scope })}>
            <option value="">{scope === "mine" ? "My zone" : "All zones"}</option>
            {zones.map((z) => (
              <option key={z.zone_id} value={z.zone_id}>
                {z.zone_name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {errors.message && <p className="error">{errors.message}</p>}
      {notices === null && <p className="muted">Loading notices...</p>}
      {notices !== null && notices.length === 0 && !errors.message && <p className="muted">No notices match these filters.</p>}

      {notices?.map((n) => (
        <Link key={n.notice_id} to={ROUTES.noticeDetails(n.notice_id)} className="card notice-row">
          <div className="card-head">
            <h2>{n.title}</h2>
            {n.targets_my_zone && <span className="badge ok">Your zone</span>}
          </div>
          <p className="muted">
            {n.published_at} | {n.event.name} | {n.zones.map((z) => z.zone_name).join(", ")}
          </p>
        </Link>
      ))}
    </section>
  );
}
