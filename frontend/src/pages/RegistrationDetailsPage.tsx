import { useEffect, useState } from "react";

import { getRegistration, updateParticipants } from "../api/registrations";
import { getHousehold } from "../api/household";
import type { Member } from "../types/api";
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

interface ParticipantEditorProps {
  details: RegistrationDetailResponse;
  onSaved: (details: RegistrationDetailResponse) => void;
  onCancel: () => void;
}

function ParticipantEditor(props: ParticipantEditorProps) {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [selectedMemberIds, setSelectedMemberIds] = useState<number[]>(
    function initialSelection() {
      const memberIds: number[] = [];

      for (const participant of props.details.participants) {
        memberIds.push(participant.member_id);
      }

      return memberIds;
    },
  );

  useEffect(function loadMembers() {
    let cancelled = false;

    async function fetchMembers() {
      try {
        const household = await getHousehold();

        if (!cancelled) {
          setMembers(household.members);
        }
      } catch (caughtError) {
        let message = "Could not load household members.";

        if (caughtError instanceof Error) {
          message = caughtError.message;
        }

        if (!cancelled) {
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void fetchMembers();

    return function cleanup() {
      cancelled = true;
    };
  }, []);

  async function saveParticipants() {
    if (saving) {
      return;
    }

    setError("");

    if (selectedMemberIds.length === 0) {
      setError("Select at least one household member.");
      return;
    }

    setSaving(true);

    try {
      await updateParticipants(
        props.details.registration.registration_id,
        {
          member_ids: selectedMemberIds,
        },
      );
    } catch (caughtError) {
      let message = "Could not update participants.";

      if (caughtError instanceof Error) {
        message = caughtError.message;
      }

      setError(message);
      setSaving(false);
      return;
    }

    // Reload the saved details so the displayed participants are current.
    try {
      const updatedDetails = await getRegistration(
        props.details.registration.registration_id,
      );

      props.onSaved(updatedDetails);
    } catch {
      setError(
        "Participants were saved, but the details could not reload. " +
        "Refresh the page to see the saved participants.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p>Loading household members...</p>;
  }

  return (
    <div>
      <h3>Select participants</h3>

      {members.map(function displayMember(member) {
        return (
          <div key={member.member_id}>
            <label>
              <input
                type="checkbox"
                checked={selectedMemberIds.includes(member.member_id)}
                disabled={saving}
                onChange={function changeMember(changeEvent) {
                  const checked = changeEvent.target.checked;

                  setError("");

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
          </div>
        );
      })}

      <p>People needing spaces: {selectedMemberIds.length}</p>

      <button
        type="button"
        onClick={saveParticipants}
        disabled={saving || members.length === 0}
      >
        {saving ? "Saving participants..." : "Save Participants"}
      </button>

      <button
        type="button"
        onClick={props.onCancel}
        disabled={saving}
      >
        Cancel
      </button>

      {error && <p role="alert">{error}</p>}
    </div>
  );
}

export default function RegistrationDetailsPage() {
  const { id = "" } = useParams();
  const [loaded, setLoaded] = useState<LoadedRegistration | null>(null);
  const [editingParticipants, setEditingParticipants] = useState(false);
  const [participantMessage, setParticipantMessage] = useState("");

  useEffect(function loadRegistration() {
    let cancelled = false;

    setEditingParticipants(false);
    setParticipantMessage("");

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
        {!editingParticipants && (
          <button
            type="button"
            disabled={
              details.registration.status.toLowerCase() !== "reserved" ||
              details.placements.length === 0 ||
              details.placements.some(function isUnavailable(placement) {
                return placement.arrival_time !== null;
              }) ||
              details.placements[details.placements.length - 1]
                .status.toLowerCase() !== "reserved" ||
              details.placements[details.placements.length - 1]
                .departure_time !== null
            }
            onClick={function openParticipantEditor() {
              setParticipantMessage("");
              setEditingParticipants(true);
            }}
          >
            Update Participants
          </button>
        )}

        {editingParticipants && (
          <ParticipantEditor
            key={id}
            details={details}
            onSaved={function finishEditing(updatedDetails) {
              setLoaded({
                id: id,
                details: updatedDetails,
                error: "",
              });
              setEditingParticipants(false);
              setParticipantMessage("Participants updated.");
            }}
            onCancel={function cancelEditing() {
              setEditingParticipants(false);
            }}
          />
        )}

        {participantMessage && (
          <p role="status">{participantMessage}</p>
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