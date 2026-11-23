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


def registration_overview(event_id=None, registration_id=None):
    """Read registrations and their children separately to avoid join multiplication."""
    from django.db import connection

    conditions, params = [], []
    for column, value in (("event_id", event_id), ("registration_id", registration_id)):
        if value is not None:
            conditions.append(f"r.{column} = %s")
            params.append(value)
    where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
    with connection.cursor() as cur:
        cur.execute('''SELECT r.registration_id, r.status, r.submitted_at,
            h.household_id, h.street, h.city, h.province, h.postal_code, h.zone_id,
            e.event_id, e.name, e.event_type, e.status, e.start_date, e.end_date,
            a.member_id, m.first_name, m.last_name, m.phone_number, a.login_email
            FROM REGISTRATION r JOIN HOUSEHOLD h ON h.household_id=r.household_id
            JOIN EMERGENCY_EVENT e ON e.event_id=r.event_id
            LEFT JOIN ACCOUNT_HOLDER a ON a.member_id=r.submitter_id
            LEFT JOIN HOUSEHOLD_MEMBER m ON m.member_id=a.member_id''' + where +
            ' ORDER BY r.submitted_at DESC, r.registration_id DESC', params)
        rows = {}
        for r in cur.fetchall():
            rows[r[0]] = {
                'registration_id': r[0], 'status': r[1], 'submitted_at': r[2].isoformat(),
                'household': dict(zip(('household_id', 'street', 'city', 'province', 'postal_code', 'zone_id'), r[3:9])),
                'event': {'event_id': r[9], 'name': r[10], 'event_type': r[11], 'status': r[12],
                          'start_date': r[13].isoformat(), 'end_date': r[14].isoformat() if r[14] else None},
                'contact': dict(zip(('member_id', 'first_name', 'last_name', 'phone_number', 'email'), r[15:20])) if r[15] else None,
                'participants': [], 'participant_count': 0, 'current_placement': None, 'placements': [],
            }
        if not rows:
            return []
        placeholders = ', '.join(['%s'] * len(rows))
        cur.execute(f'''SELECT rm.registration_id, m.member_id, m.first_name, m.last_name, m.phone_number
            FROM REGISTRATION_MEMBER rm JOIN HOUSEHOLD_MEMBER m ON m.member_id=rm.member_id
            WHERE rm.registration_id IN ({placeholders}) ORDER BY m.member_id''', list(rows))
        for r in cur.fetchall():
            rows[r[0]]['participants'].append(dict(zip(('member_id', 'first_name', 'last_name', 'phone_number'), r[1:])))
        cur.execute(f'''SELECT p.registration_id, p.placement_no, p.status, p.created_at,
            p.arrival_time, p.departure_time, s.shelter_id, s.name, s.address
            FROM PLACEMENT p JOIN SHELTER s ON s.shelter_id=p.shelter_id
            WHERE p.registration_id IN ({placeholders}) ORDER BY p.registration_id, p.placement_no''', list(rows))
        for r in cur.fetchall():
            placement = {
                'registration_id': r[0], 'placement_no': r[1], 'status': r[2],
                'created_at': r[3].isoformat(), 'arrival_time': r[4].isoformat() if r[4] else None,
                'departure_time': r[5].isoformat() if r[5] else None,
                'shelter': {'shelter_id': r[6], 'name': r[7], 'address': r[8]},
            }
            rows[r[0]]['placements'].append(placement)
        for row in rows.values():
            row['participant_count'] = len(row['participants'])
            latest = row['placements'][-1] if row['placements'] else None
            if row['status'] == 'Active' and latest and latest['status'] in ('Reserved', 'Arrived'):
                row['current_placement'] = latest
    return list(rows.values())


def shelter_identity(shelter_id):
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute('SELECT shelter_id, name, address FROM SHELTER WHERE shelter_id=%s', [shelter_id])
        row = cur.fetchone()
    return dict(zip(('shelter_id', 'name', 'address'), row)) if row else None
