"""Household shelter-registration API views."""

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.auth_helpers import api_error, household_required

@household_required
@require_http_methods(["GET"])
def registration_list(request):
    """Return registrations belonging to the logged-in household."""
    household_id = request.current_user["household_id"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT REGISTRATION.registration_id,
                REGISTRATION.event_id,
                REGISTRATION.status,
                REGISTRATION.submitted_at,
                EMERGENCY_EVENT.name
            FROM REGISTRATION
            JOIN EMERGENCY_EVENT
                ON EMERGENCY_EVENT.event_id = REGISTRATION.event_id
            WHERE REGISTRATION.household_id = %s
            ORDER BY REGISTRATION.submitted_at DESC,
                REGISTRATION.registration_id DESC
            """,
            [household_id],
        )
        rows = cursor.fetchall()

    registrations = []

    for row in rows:
        registration = {
            "registration_id": row[0],
            "event_id": row[1],
            "status": row[2],
            "submitted_at": row[3].isoformat(),
            "event_name": row[4],
        }
        registrations.append(registration)

    return JsonResponse({"registrations": registrations})

@household_required
@require_http_methods(["GET"])
def registration_detail(request, registration_id):
    """Return one registration belonging to the logged-in household."""
    household_id = request.current_user["household_id"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT REGISTRATION.registration_id,
                   REGISTRATION.event_id,
                   EMERGENCY_EVENT.name,
                   REGISTRATION.status,
                   REGISTRATION.submitted_at
            FROM REGISTRATION
            JOIN EMERGENCY_EVENT
                ON EMERGENCY_EVENT.event_id = REGISTRATION.event_id
            WHERE REGISTRATION.registration_id = %s
              AND REGISTRATION.household_id = %s
            """,
            [registration_id, household_id],
        )
        row = cursor.fetchone()

    if row is None:
        return api_error(404, "This registration was not found.")

    registration = {
        "registration_id": row[0],
        "event_id": row[1],
        "event_name": row[2],
        "status": row[3],
        "submitted_at": row[4].isoformat(),
    }

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT HOUSEHOLD_MEMBER.member_id,
                   HOUSEHOLD_MEMBER.first_name,
                   HOUSEHOLD_MEMBER.last_name
            FROM REGISTRATION_MEMBER
            JOIN HOUSEHOLD_MEMBER
                ON HOUSEHOLD_MEMBER.member_id = REGISTRATION_MEMBER.member_id
            WHERE REGISTRATION_MEMBER.registration_id = %s
            ORDER BY HOUSEHOLD_MEMBER.member_id
            """,
            [registration_id],
        )
        member_rows = cursor.fetchall()

    participants = []

    for member_row in member_rows:
        participant = {
            "member_id": member_row[0],
            "first_name": member_row[1],
            "last_name": member_row[2],
        }
        participants.append(participant)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT PLACEMENT.placement_no,
                   SHELTER.name,
                   PLACEMENT.status,
                   PLACEMENT.arrival_time,
                   PLACEMENT.departure_time
            FROM PLACEMENT
            JOIN SHELTER
                ON SHELTER.shelter_id = PLACEMENT.shelter_id
            WHERE PLACEMENT.registration_id = %s
            ORDER BY PLACEMENT.placement_no
            """,
            [registration_id],
        )
        placement_rows = cursor.fetchall()

    placements = []

    for placement_row in placement_rows:
        arrival_time = None
        departure_time = None

        if placement_row[3] is not None:
            arrival_time = placement_row[3].isoformat()

        if placement_row[4] is not None:
            departure_time = placement_row[4].isoformat()

        placement = {
            "placement_no": placement_row[0],
            "shelter_name": placement_row[1],
            "status": placement_row[2],
            "arrival_time": arrival_time,
            "departure_time": departure_time,
        }
        placements.append(placement)

    return JsonResponse({
        "registration": registration,
        "participants": participants,
        "placements": placements,
    })