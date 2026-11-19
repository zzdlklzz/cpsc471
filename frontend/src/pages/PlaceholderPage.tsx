import { useSearchParams } from "../router";

/** Temporary page for routes that Persons 2 and 3 own. They replace it with their real pages. */
export default function PlaceholderPage({ title, owner }: { title: string; owner: string }) {
  const [params] = useSearchParams();
  const eventId = params.get("event");
  return (
    <section className="card">
      <h1>{title}</h1>
      <p className="muted">This page belongs to {owner} and is not built yet.</p>
      {eventId && (
        <p>
          Selected event id: <strong>{eventId}</strong>
        </p>
      )}
    </section>
  );
}
