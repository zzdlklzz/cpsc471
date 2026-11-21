from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.auth_helpers import api_error, get_current_user, read_json, set_current_user, staff_required
from core.models import EmergencyEvent, EvacuationNotice, NoticeZone, Staff

from .queries import event_overview, registration_overview, shelter_identity
from .serializers import event_to_dict, notice_to_dict, validate_event, validate_notice


@require_http_methods(["POST"])
def login(request):
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    email = data.get("login_email")
    email = email.strip().lower() if isinstance(email, str) else ""
    password = data.get("password")
    if not email or not isinstance(password, str) or not password:
        return api_error(400, "Enter your email and password.")

    staff = Staff.objects.filter(login_email__iexact=email).first()
    if staff is not None and check_password(password, staff.password_hash):
        set_current_user(request, {"role": "staff", "staff_id": staff.staff_id})
        return JsonResponse(get_current_user(request))
    return api_error(401, "The email or password is not correct.")


@staff_required
@require_http_methods(["GET", "POST"])
def events(request):
    if request.method == "POST":
        data = read_json(request)
        if data is None:
            return api_error(400, "Send JSON data.")
        clean, errors = validate_event(data)
        if errors:
            return api_error(400, "Please correct the highlighted fields.", errors)
        event = EmergencyEvent.objects.create(**clean)
        return JsonResponse(event_to_dict(event), status=201)
    status = request.GET.get("status")
    if status is not None and status not in ("Active", "Closed"):
        return api_error(400, "Choose Active or Closed for status.")
    return JsonResponse({"events": event_overview(status)})


@staff_required
@require_http_methods(["PATCH"])
def event_detail(request, event_id):
    event = EmergencyEvent.objects.filter(pk=event_id).first()
    if event is None:
        return api_error(404, "This event was not found.")
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    clean, errors = validate_event(data, instance=event)
    if errors:
        return api_error(400, "Please correct the highlighted fields.", errors)
    for field, value in clean.items():
        setattr(event, field, value)
    if clean:
        event.save(update_fields=list(clean))
    return JsonResponse(event_to_dict(event))


@staff_required
@require_http_methods(["POST"])
def notices(request):
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    clean, errors = validate_notice(data)
    if errors:
        return api_error(400, "Please correct the highlighted fields.", errors)
    zone_ids = clean.pop("zone_ids")
    with transaction.atomic():
        notice = EvacuationNotice.objects.create(
            **clean, staff_id=request.current_user["staff_id"],
            published_at=timezone.now().replace(microsecond=0))
        NoticeZone.objects.bulk_create([NoticeZone(notice=notice, zone_id=z) for z in zone_ids])
    return JsonResponse(notice_to_dict(notice), status=201)


@staff_required
@require_http_methods(["PATCH"])
def notice_detail(request, notice_id):
    notice = EvacuationNotice.objects.filter(pk=notice_id).first()
    if notice is None:
        return api_error(404, "This notice was not found.")
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    clean, errors = validate_notice(data, instance=notice)
    if errors:
        return api_error(400, "Please correct the highlighted fields.", errors)
    zone_ids = clean.pop("zone_ids", None)
    with transaction.atomic():
        for field, value in clean.items():
            setattr(notice, field, value)
        if clean:
            notice.save(update_fields=list(clean))
        if zone_ids is not None:
            NoticeZone.objects.filter(notice=notice).delete()
            NoticeZone.objects.bulk_create([NoticeZone(notice=notice, zone_id=z) for z in zone_ids])
    return JsonResponse(notice_to_dict(notice))


def _read_id_filters(request, names):
    filters = {}
    for name in names:
        raw = request.GET.get(name)
        if raw is not None:
            if len(raw) > 10 or not raw.isascii() or not raw.isdecimal() or not 0 < int(raw) <= 2147483647:
                return None
            filters[name] = int(raw)
    return filters


@staff_required
@require_http_methods(["GET"])
def registrations(request):
    filters = _read_id_filters(request, ("event_id", "registration_id"))
    if filters is None:
        return api_error(400, "Use positive integer IDs for filters.")
    rows = registration_overview(**filters)
    return JsonResponse({"registrations": [{k: v for k, v in row.items() if k != "placements"} for row in rows]})


@staff_required
@require_http_methods(["GET"])
def registration_detail(request, registration_id):
    rows = registration_overview(registration_id=registration_id)
    if not rows:
        return api_error(404, "This registration was not found.")
    return JsonResponse(rows[0])


@staff_required
@require_http_methods(["GET"])
def shelter_placements(request, shelter_id):
    filters = _read_id_filters(request, ("event_id",))
    view = request.GET.get("view", "reservations")
    if filters is None or view not in ("reservations", "occupants", "history"):
        return api_error(400, "Choose a valid view and positive integer event ID.")
    shelter = shelter_identity(shelter_id)
    if shelter is None:
        return api_error(404, "This shelter was not found.")
    placements = []
    for row in registration_overview(**filters):
        for placement in row['placements']:
            if placement['shelter']['shelter_id'] != shelter_id:
                continue
            if view != 'history':
                expected = 'Reserved' if view == 'reservations' else 'Arrived'
                if placement != row['current_placement'] or placement['status'] != expected:
                    continue
            placements.append({**placement, 'registration_status': row['status'],
                               **{k: row[k] for k in ('household', 'event', 'contact', 'participants', 'participant_count')}})
    return JsonResponse({'shelter': shelter, 'view': view, 'placements': placements})
