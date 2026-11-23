from datetime import date

from core.models import EmergencyEvent, EvacuationZone


def event_to_dict(event):
    return {
        "event_id": event.event_id, "name": event.name,
        "event_type": event.event_type, "status": event.status,
        "start_date": event.start_date.isoformat(),
        "end_date": event.end_date.isoformat() if event.end_date else None,
    }


def validate_event(data, instance=None):
    """Validate supplied fields and the resulting date range before any write."""
    clean, errors = {}, {}
    for field in ("name", "event_type", "status"):
        if instance is not None and field not in data:
            continue
        value = data.get(field, "Active" if field == "status" else None)
        if not isinstance(value, str) or not value.strip():
            errors[field] = "Enter a nonblank string."
            continue
        value = value.strip()
        if field == "name" and len(value) > 100:
            errors[field] = "Use at most 100 characters."
        elif field == "event_type" and value not in ("Wildfire", "Flood"):
            errors[field] = "Choose Wildfire or Flood."
        elif field == "status" and value not in ("Active", "Closed"):
            errors[field] = "Choose Active or Closed."
        else:
            clean[field] = value

    for field in ("start_date", "end_date"):
        if instance is not None and field not in data:
            continue
        value = data.get(field)
        if field == "end_date" and value is None:
            clean[field] = None
            continue
        try:
            parsed = date.fromisoformat(value) if isinstance(value, str) else None
            if parsed is None or parsed.isoformat() != value:
                raise ValueError
            clean[field] = parsed
        except ValueError:
            errors[field] = "Use a valid YYYY-MM-DD date."

    start = clean.get("start_date", getattr(instance, "start_date", None))
    end = clean.get("end_date", getattr(instance, "end_date", None))
    if not errors and start and end and end < start:
        errors["end_date"] = "End date must be on or after start date."
    return clean, errors


def notice_to_dict(notice):
    return {
        "notice_id": notice.pk, "title": notice.title, "message": notice.message,
        "published_at": notice.published_at.isoformat(),
        "event": event_to_dict(notice.event),
        "publisher": {"staff_id": notice.staff_id, "name": notice.staff.name},
        "zones": list(EvacuationZone.objects.filter(notice_zones__notice_id=notice.pk)
                      .order_by("zone_name", "zone_id").values("zone_id", "zone_name")),
    }


def validate_notice(data, instance=None):
    clean, errors = {}, {}
    for field in ("title", "message"):
        if instance is not None and field not in data:
            continue
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors[field] = "Enter a nonblank string."
        elif field == "title" and len(value.strip()) > 150:
            errors[field] = "Use at most 150 characters."
        else:
            clean[field] = value.strip()
    if instance is None:
        event_id = data.get("event_id")
        if type(event_id) is not int or event_id <= 0:
            errors["event_id"] = "Choose a valid event ID."
        elif not EmergencyEvent.objects.filter(pk=event_id).exists():
            errors["event_id"] = "This event was not found."
        else:
            clean["event_id"] = event_id
    if instance is None or "zone_ids" in data:
        ids = data.get("zone_ids")
        if not isinstance(ids, list) or not ids or any(type(i) is not int or i <= 0 for i in ids):
            errors["zone_ids"] = "Choose at least one valid zone ID."
        else:
            ids = list(dict.fromkeys(ids))
            if EvacuationZone.objects.filter(pk__in=ids).count() != len(ids):
                errors["zone_ids"] = "One or more zones were not found."
            else:
                clean["zone_ids"] = ids
    return clean, errors
