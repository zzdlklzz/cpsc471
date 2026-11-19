"""Read-only notice pages for Person 1. Person 3 owns creating and editing events and notices."""
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.auth_helpers import api_error, login_required_api
from core.models import EmergencyEvent, EvacuationNotice, Household

# Assumption to confirm with the team: only Active events accept new registrations.
REGISTRATION_OPEN_STATUS = "Active"


def _notice_ids_for_zone(zone_id):
    with connection.cursor() as cur:
        cur.execute("SELECT notice_id FROM NOTICE_ZONE WHERE zone_id = %s", [zone_id])
        return [row[0] for row in cur.fetchall()]


def _zones_by_notice(notice_ids):
    """Returns {notice_id: [{"zone_id":..., "zone_name":...}, ...]}."""
    result = {notice_id: [] for notice_id in notice_ids}
    if not notice_ids:
        return result
    placeholders = ", ".join(["%s"] * len(notice_ids))
    with connection.cursor() as cur:
        cur.execute(
            "SELECT nz.notice_id, z.zone_id, z.zone_name FROM NOTICE_ZONE nz"
            " JOIN EVACUATION_ZONE z ON z.zone_id = nz.zone_id"
            f" WHERE nz.notice_id IN ({placeholders}) ORDER BY z.zone_name",
            list(notice_ids))
        for notice_id, zone_id, zone_name in cur.fetchall():
            result[notice_id].append({"zone_id": zone_id, "zone_name": zone_name})
    return result


def _home_zone_id(user):
    if user["role"] != "household":
        return None
    return Household.objects.values_list("zone_id", flat=True).get(pk=user["household_id"])


def _notice_to_dict(notice, zones, home_zone_id):
    return {
        "notice_id": notice.notice_id,
        "title": notice.title,
        "message": notice.message,
        "published_at": notice.published_at.strftime("%Y-%m-%d %H:%M"),
        "event": {"event_id": notice.event.event_id, "name": notice.event.name,
                  "event_type": notice.event.event_type, "status": notice.event.status},
        "zones": zones,
        "targets_my_zone": any(z["zone_id"] == home_zone_id for z in zones),
        "can_register": notice.event.status == REGISTRATION_OPEN_STATUS,
    }


def _int_param(request, name):
    """Returns (value or None, ok)."""
    raw = request.GET.get(name)
    if raw in (None, ""):
        return None, True
    return (int(raw), True) if raw.isdigit() else (None, False)


@login_required_api
@require_http_methods(["GET"])
def events(request):
    """Event list for the filter. Read only. Person 3 owns the create and edit operations."""
    rows = EmergencyEvent.objects.order_by("-start_date", "-event_id")
    return JsonResponse({"events": [
        {"event_id": e.event_id, "name": e.name, "event_type": e.event_type, "status": e.status,
         "start_date": e.start_date.isoformat(),
         "end_date": e.end_date.isoformat() if e.end_date else None} for e in rows]})


@login_required_api
@require_http_methods(["GET"])
def notice_list(request):
    """?scope=mine (default, notices for the home zone) or all. Optional ?event=<id>&zone=<id>."""
    user = request.current_user
    home_zone_id = _home_zone_id(user)
    event_id, ok1 = _int_param(request, "event")
    zone_id, ok2 = _int_param(request, "zone")
    scope = request.GET.get("scope", "mine")
    if not (ok1 and ok2) or scope not in ("mine", "all"):
        return api_error(400, "The filter values are not valid.")

    notices = EvacuationNotice.objects.select_related("event")
    if zone_id is not None:
        notices = notices.filter(notice_id__in=_notice_ids_for_zone(zone_id))
    elif scope == "mine" and home_zone_id is not None:
        notices = notices.filter(notice_id__in=_notice_ids_for_zone(home_zone_id))
    if event_id is not None:
        notices = notices.filter(event_id=event_id)
    notices = list(notices.order_by("-published_at", "-notice_id"))     # newest first

    zones = _zones_by_notice([n.notice_id for n in notices])
    return JsonResponse({"notices": [_notice_to_dict(n, zones[n.notice_id], home_zone_id)
                                     for n in notices]})


@login_required_api
@require_http_methods(["GET"])
def notice_detail(request, notice_id):
    notice = EvacuationNotice.objects.select_related("event").filter(pk=notice_id).first()
    if notice is None:
        return api_error(404, "This notice was not found.")
    zones = _zones_by_notice([notice.notice_id])[notice.notice_id]
    return JsonResponse(_notice_to_dict(notice, zones, _home_zone_id(request.current_user)))
