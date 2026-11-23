import { useEffect, useState } from "react";

import { getRegistration } from "../api/registrations";
import { Link, useParams } from "../router";
import { ROUTES } from "../routes";
import type { RegistrationDetailResponse } from "../types/registration";

interface LoadedRegistration {
  id: string;
  details: RegistrationDetailResponse | null;
  error: string;
}

function displayTime(value: string | null): string {
  if (value === null) {
    return "Not recorded";
  }

  return new Date(value).toLocaleString();
}

export default function RegistrationDetailsPage() {
  const { id = "" } = useParams();
  const [loaded, setLoaded] = useState<LoadedRegistration | null>(null);

  useEffect(function loadRegistration() {
    let cancelled = false;

    async function fetchRegistration() {
      try {
        const details = await getRegistration(Number(id));

        if (!cancelled) {
          setLoaded({
            id: id,
            details: details,
            error: "",
          });
        }
      } catch (caughtError) {
        let message = "Could not load this registration.";

        if (caughtError instanceof Error) {
          message = caughtError.message;
        }

        if (!cancelled) {
          setLoaded({
            id: id,
            details: null,
            error: message,
          });
        }
      }
    }

    void fetchRegistration();

    return function cleanup() {
      cancelled = true;
    };
  }, [id]);

  if (loaded === null || loaded.id !== id) {
    return <p className="muted">Loading registration...</p>;
  }

  const details = loaded.details;

  if (details === null) {
    return (
      <section>
        <p className="error" role="alert">{loaded.error}</p>
        <Link to={ROUTES.shelter}>Back to My Shelter</Link>
      </section>
    );
  }

  return (
    <section>
      <Link to={ROUTES.shelter}>Back to My Shelter</Link>

      <div className="card">
        <h1>{details.registration.event_name}</h1>
        <p>Registration status: {details.registration.status}</p>
        <p>
          Submitted: {displayTime(details.registration.submitted_at)}
        </p>
      </div>

      <div className="card">
        <h2>Participants</h2>

        {details.participants.length === 0 ? (
          <p>No participants recorded.</p>
        ) : (
          <ul>
            {details.participants.map(function renderParticipant(participant) {
              return (
                <li key={participant.member_id}>
                  {participant.first_name} {participant.last_name}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="card">
        <h2>Placement History</h2>

        {details.placements.length === 0 ? (
          <p>No placements recorded.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Shelter</th>
                <th>Status</th>
                <th>Arrival</th>
                <th>Departure</th>
              </tr>
            </thead>

            <tbody>
              {details.placements.map(function renderPlacement(placement) {
                return (
                  <tr key={placement.placement_no}>
                    <td>{placement.shelter_name}</td>
                    <td>{placement.status}</td>
                    <td>{displayTime(placement.arrival_time)}</td>
                    <td>{displayTime(placement.departure_time)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}