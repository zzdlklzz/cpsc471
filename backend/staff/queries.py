from core.models import EmergencyEvent, EvacuationNotice, NoticeZone

from .serializers import event_to_dict


def event_overview(status=None):
    events = EmergencyEvent.objects.order_by("-start_date", "-event_id")
    if status is not None:
        events = events.filter(status=status)
    rows = {}
    for event in events:
        rows[event.event_id] = {**event_to_dict(event), "notices": []}

    notices = list(EvacuationNotice.objects.filter(event_id__in=rows)
                   .select_related("staff").order_by("-published_at", "-notice_id"))
    zones = {notice.notice_id: [] for notice in notices}
    targets = (NoticeZone.objects.filter(notice_id__in=zones).select_related("zone")
               .order_by("zone__zone_name", "zone_id"))
    for target in targets:
        zones[target.notice_id].append({"zone_id": target.zone_id, "zone_name": target.zone.zone_name})
    for notice in notices:
        event = rows[notice.event_id]
        event["notices"].append({
            "notice_id": notice.notice_id, "title": notice.title, "message": notice.message,
            "published_at": notice.published_at.isoformat(),
            "event": {key: value for key, value in event.items() if key != "notices"},
            "publisher": {"staff_id": notice.staff_id, "name": notice.staff.name},
            "zones": zones[notice.notice_id],
        })
    return list(rows.values())
