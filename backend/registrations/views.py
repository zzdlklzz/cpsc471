"""Household shelter-registration API views."""

from django.db import connection, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.auth_helpers import api_error, household_required, read_json

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

@household_required
@require_http_methods(["GET"])
def shelter_list(request):
    """Return open shelters with staff and enough available spaces."""
    raw_group_size = request.GET.get("group_size", "")

    try:
        group_size = int(raw_group_size)
    except ValueError:
        return api_error(400, "Choose at least one household member.")

    if group_size < 1:
        return api_error(400, "Choose at least one household member.")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT shelter_id, name, address, available_spaces
            FROM SHELTER
            WHERE operating_status = 'Open'
              AND available_spaces >= %s
              AND EXISTS (
                  SELECT 1
                  FROM MANAGES
                  WHERE MANAGES.shelter_id = SHELTER.shelter_id
              )
            ORDER BY name, shelter_id
            """,
            [group_size],
        )
        rows = cursor.fetchall()

    shelters = []

    for row in rows:
        shelter = {
            "shelter_id": row[0],
            "name": row[1],
            "address": row[2],
            "available_spaces": row[3],
        }
        shelters.append(shelter)

    return JsonResponse({"shelters": shelters})

@household_required
@require_http_methods(["POST"])
def create_registration(request):
    """Reserve shelter spaces for selected household members."""
    data = read_json(request)

    if data is None:
        return api_error(400, "Send a valid JSON object.")

    event_id = data.get("event_id")
    shelter_id = data.get("shelter_id")
    member_ids = data.get("member_ids")

    # Use type(...) rather than isinstance(...) here because Python
    # otherwise treats True and False as integers.
    if type(event_id) is not int or event_id < 1:
        return api_error(400, "Choose a valid event.")

    if type(shelter_id) is not int or shelter_id < 1:
        return api_error(400, "Choose a valid shelter.")

    if not isinstance(member_ids, list) or len(member_ids) == 0:
        return api_error(400, "Select at least one household member.")

    for member_id in member_ids:
        if type(member_id) is not int or member_id < 1:
            return api_error(400, "Select valid household members.")

    if len(member_ids) != len(set(member_ids)):
        return api_error(400, "Do not select the same member twice.")

    household_id = request.current_user["household_id"]
    submitter_id = request.current_user["member_id"]
    group_size = len(member_ids)

    # All changes succeed together or are rolled back together.
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Lock this household so two simultaneous requests from it
            # cannot create duplicate registrations.
            cursor.execute(
                """
                SELECT household_id
                FROM HOUSEHOLD
                WHERE household_id = %s
                FOR UPDATE
                """,
                [household_id],
            )

            if cursor.fetchone() is None:
                return api_error(404, "This household was not found.")

            cursor.execute(
                """
                SELECT status
                FROM EMERGENCY_EVENT
                WHERE event_id = %s
                FOR SHARE
                """,
                [event_id],
            )
            event = cursor.fetchone()

            if event is None:
                return api_error(404, "This event was not found.")

            if event[0].lower() != "active":
                return api_error(400, "This event is no longer active.")

            cursor.execute(
                """
                SELECT registration_id
                FROM REGISTRATION
                WHERE household_id = %s
                  AND event_id = %s
                FOR UPDATE
                """,
                [household_id, event_id],
            )

            if cursor.fetchone() is not None:
                return api_error(
                    409,
                    "Your household already has a registration for this event.",
                )

            # Read and lock the household's members, then check that
            # every requested participant belongs to this household.
            cursor.execute(
                """
                SELECT member_id
                FROM HOUSEHOLD_MEMBER
                WHERE household_id = %s
                FOR UPDATE
                """,
                [household_id],
            )
            member_rows = cursor.fetchall()

            household_member_ids = set()

            for member_row in member_rows:
                household_member_ids.add(member_row[0])

            for member_id in member_ids:
                if member_id not in household_member_ids:
                    return api_error(
                        400,
                        "Every participant must belong to your household.",
                    )

            # Lock the shelter before checking capacity. Another booking
            # must wait until this transaction finishes.
            cursor.execute(
                """
                SELECT operating_status, available_spaces
                FROM SHELTER
                WHERE shelter_id = %s
                FOR UPDATE
                """,
                [shelter_id],
            )
            shelter = cursor.fetchone()

            if shelter is None:
                return api_error(404, "This shelter was not found.")

            if shelter[0].lower() != "open":
                return api_error(409, "This shelter is no longer open.")

            if shelter[1] < group_size:
                return api_error(
                    409,
                    "This shelter no longer has enough available spaces. "
                    "Search again.",
                )

            cursor.execute(
                """
                SELECT staff_id
                FROM MANAGES
                WHERE shelter_id = %s
                FOR SHARE
                """,
                [shelter_id],
            )

            if cursor.fetchone() is None:
                return api_error(
                    409,
                    "This shelter no longer has assigned staff.",
                )

            # Validation is finished. Start saving the reservation.
            cursor.execute(
                """
                INSERT INTO REGISTRATION
                    (status, household_id, event_id, submitter_id)
                VALUES (%s, %s, %s, %s)
                """,
                ["Reserved", household_id, event_id, submitter_id],
            )
            registration_id = cursor.lastrowid

            for member_id in member_ids:
                cursor.execute(
                    """
                    INSERT INTO REGISTRATION_MEMBER
                        (registration_id, member_id)
                    VALUES (%s, %s)
                    """,
                    [registration_id, member_id],
                )

            cursor.execute(
                """
                INSERT INTO PLACEMENT
                    (registration_id, placement_no, status, shelter_id)
                VALUES (%s, %s, %s, %s)
                """,
                [registration_id, 1, "Reserved", shelter_id],
            )

            cursor.execute(
                """
                UPDATE SHELTER
                SET available_spaces = available_spaces - %s
                WHERE shelter_id = %s
                """,
                [group_size, shelter_id],
            )

    return JsonResponse(
        {
            "registration_id": registration_id,
            "message": "Your shelter reservation is confirmed.",
        },
        status=201,
    )

@household_required
@require_http_methods(["PATCH"])
def update_participants(request, registration_id):
    """Update participants before check-in and adjust shelter spaces."""
    data = read_json(request)

    if data is None:
        return api_error(400, "Send a valid JSON object.")

    member_ids = data.get("member_ids")

    if not isinstance(member_ids, list) or len(member_ids) == 0:
        return api_error(400, "Select at least one household member.")

    for member_id in member_ids:
        if type(member_id) is not int or member_id < 1:
            return api_error(400, "Select valid household members.")

    if len(member_ids) != len(set(member_ids)):
        return api_error(400, "Do not select the same member twice.")

    household_id = request.current_user["household_id"]

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT household_id
                FROM HOUSEHOLD
                WHERE household_id = %s
                FOR UPDATE
                """,
                [household_id],
            )

            if cursor.fetchone() is None:
                return api_error(404, "This household was not found.")

            # Check ownership and prevent simultaneous changes.
            cursor.execute(
                """
                SELECT status
                FROM REGISTRATION
                WHERE registration_id = %s
                  AND household_id = %s
                FOR UPDATE
                """,
                [registration_id, household_id],
            )
            registration = cursor.fetchone()

            if registration is None:
                return api_error(404, "This registration was not found.")

            if registration[0].lower() != "reserved":
                return api_error(
                    409,
                    "Participants can only be changed for a reserved registration.",
                )

            cursor.execute(
                """
                SELECT member_id
                FROM HOUSEHOLD_MEMBER
                WHERE household_id = %s
                FOR UPDATE
                """,
                [household_id],
            )
            member_rows = cursor.fetchall()

            household_member_ids = set()

            for member_row in member_rows:
                household_member_ids.add(member_row[0])

            for member_id in member_ids:
                if member_id not in household_member_ids:
                    return api_error(
                        400,
                        "Every participant must belong to your household.",
                    )

            # Check all placements so a previous check-in also blocks editing.
            cursor.execute(
                """
                SELECT placement_no,
                       shelter_id,
                       status,
                       arrival_time,
                       departure_time
                FROM PLACEMENT
                WHERE registration_id = %s
                ORDER BY placement_no
                FOR UPDATE
                """,
                [registration_id],
            )
            placements = cursor.fetchall()

            if len(placements) == 0:
                return api_error(409, "This registration has no placement.")

            for placement in placements:
                if placement[3] is not None:
                    return api_error(
                        409,
                        "Participants cannot be changed after check-in.",
                    )

            latest_placement = placements[-1]

            if (
                latest_placement[2].lower() != "reserved"
                or latest_placement[4] is not None
            ):
                return api_error(
                    409,
                    "This placement is no longer reserved.",
                )

            shelter_id = latest_placement[1]

            cursor.execute(
                """
                SELECT member_id
                FROM REGISTRATION_MEMBER
                WHERE registration_id = %s
                FOR UPDATE
                """,
                [registration_id],
            )
            current_members = cursor.fetchall()

            old_group_size = len(current_members)
            new_group_size = len(member_ids)
            extra_spaces_needed = new_group_size - old_group_size

            cursor.execute(
                """
                SELECT available_spaces, capacity
                FROM SHELTER
                WHERE shelter_id = %s
                FOR UPDATE
                """,
                [shelter_id],
            )
            shelter = cursor.fetchone()

            if shelter is None:
                return api_error(404, "This shelter was not found.")

            updated_spaces = shelter[0] - extra_spaces_needed

            if updated_spaces < 0:
                return api_error(
                    409,
                    "This shelter does not have enough spaces "
                    "for the additional participants.",
                )

            if updated_spaces > shelter[1]:
                return api_error(
                    409,
                    "Shelter availability is inconsistent. Contact staff.",
                )

            # All checks passed. Replace the participant list.
            cursor.execute(
                """
                DELETE FROM REGISTRATION_MEMBER
                WHERE registration_id = %s
                """,
                [registration_id],
            )

            for member_id in member_ids:
                cursor.execute(
                    """
                    INSERT INTO REGISTRATION_MEMBER
                        (registration_id, member_id)
                    VALUES (%s, %s)
                    """,
                    [registration_id, member_id],
                )

            cursor.execute(
                """
                UPDATE SHELTER
                SET available_spaces = %s
                WHERE shelter_id = %s
                """,
                [updated_spaces, shelter_id],
            )

    return JsonResponse({
        "message": "Participants updated.",
    })