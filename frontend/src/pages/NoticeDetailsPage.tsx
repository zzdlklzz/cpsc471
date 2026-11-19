import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { getNotice } from "../api/notices";
import { useAuth } from "../context/authContext";
import { Link, useNavigate, useParams } from "../router";
import { ROUTES } from "../routes";
import type { Notice } from "../types/api";

/** The answer for one notice id: the notice, or an error message. */
interface Loaded {
  id: string;
  notice: Notice | null;
  error: string;
}

export default function NoticeDetailsPage() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState<Loaded | null>(null);

  useEffect(() => {
    let cancelled = false;
    getNotice(Number(id))
      .then((notice) => {
        if (!cancelled) setLoaded({ id, notice, error: "" });
      })
      .catch((err: unknown) => {
        const error = err instanceof ApiError ? err.message : "Something went wrong.";
        if (!cancelled) setLoaded({ id, notice: null, error });
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const current = loaded && loaded.id === id ? loaded : null;
  if (!current) return <p className="muted">Loading notice...</p>;

  const notice = current.notice;
  if (!notice) {
    return (
      <section>
        <p className="error">{current.error}</p>
        <Link to={ROUTES.notices}>Back to notices</Link>
      </section>
    );
  }

  return (
    <section>
      <Link to={ROUTES.notices}>Back to notices</Link>
      <div className="card">
        <h1>{notice.title}</h1>
        <p className="muted">Published {notice.published_at}</p>
        <p className="message">{notice.message}</p>
        <p>
          <strong>Event:</strong> {notice.event.name} ({notice.event.event_type}, {notice.event.status})
        </p>
        <p>
          <strong>Affected zones:</strong> {notice.zones.map((z) => z.zone_name).join(", ")}
          {notice.targets_my_zone && <span className="badge ok">Includes your zone</span>}
        </p>
        {user?.role === "household" &&
          (notice.can_register ? (
            // This only opens Person 2's flow with the event selected. It does not reserve anything.
            <button type="button" onClick={() => navigate(ROUTES.shelterRegister(notice.event.event_id))}>
              Register for Shelter
            </button>
          ) : (
            <p className="muted">This event is closed, so registration is not available.</p>
          ))}
      </div>
    </section>
  );
}
