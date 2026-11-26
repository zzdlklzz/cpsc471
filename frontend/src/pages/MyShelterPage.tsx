import { useEffect, useState } from "react";

import { getRegistrations } from "../api/registrations";
import type { Registration } from "../types/registration";
import { Link } from "../router";

export default function MyShelterPage() {
  const [registrations, setRegistrations] = useState<Registration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(function loadRegistrations() {
    let active = true;

    async function fetchRegistrations() {
      try {
        const response = await getRegistrations();

        if (active) {
          setRegistrations(response.registrations);
        }
      } catch (caughtError) {
        if (active) {
          let message = "Could not load registrations.";

          if (caughtError instanceof Error) {
            message = caughtError.message;
          }

          setError(message);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void fetchRegistrations();

    return function cleanup() {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <section>
        <h1>My Shelter</h1>
        <p>Loading registrations...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section>
        <h1>My Shelter</h1>
        <p role="alert">{error}</p>
      </section>
    );
  }

  if (registrations.length === 0) {
    return (
      <section>
        <h1>My Shelter</h1>
        <p>No registrations yet.</p>
      </section>
    );
  }

  return (
    <section>
      <h1>My Shelter</h1>

      <table>
        <thead>
          <tr>
            <th>Registration</th>
            <th>Event</th>
            <th>Status</th>
            <th>Submitted</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {registrations.map(function renderRegistration(registration) {
            return (
              <tr key={registration.registration_id}>
                <td>{registration.registration_id}</td>
                <td>{registration.event_name}</td>
                <td>{registration.status}</td>
                <td>
                  {new Date(registration.submitted_at).toLocaleString()}
                </td>
                <td>
                  <Link to={"/shelter/registrations/" + registration.registration_id}>
                  View details
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}