import { useEffect, useState } from "react";

import { getHousehold } from "../api/household";
import { getEvents } from "../api/notices";
import type { EventSummary, Member } from "../types/api";
import { getShelters } from "../api/registrations";
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

  async function findShelters() {
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
    disabled={searching}
    onChange={function changeEvent(changeEvent) {
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
          {event.name}
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

      <button type="button" onClick={findShelters} disabled={searching}>
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
                <h3>{shelter.name}</h3>
                <p>{shelter.address}</p>
                <p>Available spaces: {shelter.available_spaces}</p>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}