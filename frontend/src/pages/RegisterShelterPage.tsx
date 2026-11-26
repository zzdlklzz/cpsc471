import { useEffect, useState } from "react";

import { getHousehold } from "../api/household";
import { getEvents } from "../api/notices";
import type { EventSummary, Member } from "../types/api";
import { createRegistration, getShelters, } from "../api/registrations";
import type { Shelter } from "../types/registration";

export default function RegisterShelterPage() {
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedEventId, setSelectedEventId] = useState("");
  const [selectedMemberIds, setSelectedMemberIds] = useState<number[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchComplete, setSearchComplete] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [selectedShelterId, setSelectedShelterId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [reservationError, setReservationError] = useState("");
  const [reservationSuccess, setReservationSuccess] = useState("");

async function confirmReservation() {
  if (saving || reservationSuccess !== "") {
    return;
  }

  setReservationError("");

  if (selectedEventId === "") {
    setReservationError("Choose an event.");
    return;
  }

  if (selectedMemberIds.length === 0) {
    setReservationError("Select at least one household member.");
    return;
  }

  if (selectedShelterId === null) {
    setReservationError("Select a shelter.");
    return;
  }

  setSaving(true);

  try {
    const response = await createRegistration({
      event_id: Number(selectedEventId),
      shelter_id: selectedShelterId,
      member_ids: selectedMemberIds,
    });

    setReservationSuccess(response.message);
    setSearchComplete(false);
    setShelters([]);
    setSelectedShelterId(null);
  } catch (caughtError) {
    let message = "Could not save your reservation.";

    if (caughtError instanceof Error) {
      message = caughtError.message;
    }

    setReservationError(message);
  } finally {
    setSaving(false);
  }
}

  async function findShelters() {
  setSelectedShelterId(null);
  setReservationError("");
  setSearchError("");
  setSearchComplete(false);
  setShelters([]);

  if (selectedEventId === "") {
    setSearchError("Choose an event.");
    return;
  }

  if (selectedMemberIds.length === 0) {
    setSearchError("Select at least one household member.");
    return;
  }

  setSearching(true);

  try {
    const response = await getShelters(selectedMemberIds.length);

    setShelters(response.shelters);
    setSearchComplete(true);
  } catch (caughtError) {
    let message = "Could not load shelters.";

    if (caughtError instanceof Error) {
      message = caughtError.message;
    }

    setSearchError(message);
  } finally {
    setSearching(false);
  }
}

  useEffect(function loadPage() {
    let active = true;

    async function fetchPageData() {
      try {
        const household = await getHousehold();
        const eventList = await getEvents();

        if (active) {
          setMembers(household.members);
          setEvents(eventList);

          const searchParameters = new URLSearchParams(
            window.location.search,
          );
          const requestedEventId = searchParameters.get("event_id");

          if (requestedEventId !== null) {
            let matchingEventFound = false;

            for (const event of eventList) {
              if (
                String(event.event_id) === requestedEventId &&
                event.status.toLowerCase() === "active"
              ) {
                setSelectedEventId(String(event.event_id));
                matchingEventFound = true;
                break;
              }
            }

            if (!matchingEventFound) {
              setSearchError(
                "The linked event is unavailable. Choose an active event.",
              );
            }
          }
        }
      } catch (caughtError) {
        if (active) {
          let message = "Could not load events and household members.";

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

    void fetchPageData();

    return function cleanup() {
      active = false;
    };
  }, []);

  if (loading) {
    return <p>Loading events and household members...</p>;
  }

  if (error) {
    return <p role="alert">{error}</p>;
  }

  return (
    <section>
      <h1>Register for Shelter</h1>

        <div className="card">
            <h2>Choose an event</h2>

            <label htmlFor="event">Emergency event</label>

  <select
    id="event"
    value={selectedEventId}
    disabled={searching || saving || reservationSuccess !== ""}
    onChange={function changeEvent(changeEvent) {
      setSelectedShelterId(null);
      setReservationError("");
      setSelectedEventId(changeEvent.target.value);
      setSearchComplete(false);
      setShelters([]);
      setSearchError("");
    }
  }
>
    <option value="">Select an event</option>

    {events.map(function displayEvent(event) {
      if (event.status.toLowerCase() !== "active") {
        return null;
      }

      return (
        <option key={event.event_id} value={event.event_id}>
          {event.name} (Event {event.event_id})
        </option>
      );
    })}
  </select>
</div>

<div className="card">
  <h2>Select household members</h2>

  {members.length === 0 && <p>No household members found.</p>}

  {members.map(function displayMember(member) {
    return (
      <label key={member.member_id}>
        <input
          type="checkbox"
          disabled={searching}
          checked={selectedMemberIds.includes(member.member_id)}
          onChange={function changeMember(changeEvent) {
            setSelectedShelterId(null);
            setReservationError("");
              const checked = changeEvent.target.checked;
            setSearchComplete(false);
            setShelters([]);
            setSearchError("");

            setSelectedMemberIds(function updateSelection(currentIds) {
              const updatedIds: number[] = [];

              for (const memberId of currentIds) {
                if (memberId !== member.member_id) {
                  updatedIds.push(memberId);
                }
              }

              if (checked) {
                updatedIds.push(member.member_id);
              }

              return updatedIds;
            });
          }}
        />
        {member.first_name} {member.last_name}
      </label>
    );
  })}

        <p>People needing spaces: {selectedMemberIds.length}</p>
      </div>

      <button type="button" onClick={findShelters} disabled={searching || saving || reservationSuccess !== ""}>
        Find shelters
      </button>

      {searching && <p>Searching for shelters...</p>}

      {searchError && <p role="alert">{searchError}</p>}

      {searchComplete && (
        <div className="card">
          <h2>Available shelters</h2>

          {shelters.length === 0 && (
            <p>No eligible shelter has enough available spaces.</p>
          )}

{shelters.map(function displayShelter(shelter) {
  return (
    <div key={shelter.shelter_id}>
      <label>
        <input
          type="radio"
          name="shelter"
          value={shelter.shelter_id}
          checked={selectedShelterId === shelter.shelter_id}
          disabled={searching || saving || reservationSuccess !== ""}
          onChange={function changeShelter() {
            setSelectedShelterId(shelter.shelter_id);
            setReservationError("");
          }}
        />
        {shelter.name}
      </label>

      <p>{shelter.address}</p>
      <p>Available spaces: {shelter.available_spaces}</p>
    </div>
  );
})}

{shelters.length > 0 && (
  <button
    type="button"
    onClick={confirmReservation}
    disabled={saving || reservationSuccess !== ""}
  >
    {saving ? "Saving reservation..." : "Confirm Reservation"}
  </button>
)}
        </div>
      )}
      {reservationError && (
        <p role="alert">{reservationError}</p>
      )}

      {reservationSuccess && (
        <p role="status">{reservationSuccess}</p>
      )}
    </section>
  );
}