import json

from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.test import Client, RequestFactory, TestCase

from core import testing as t
from core.auth_helpers import staff_required


class LoginTests(TestCase):
    def setUp(self):
        zone = t.make_zone()
        _, self.member, self.holder = t.make_household(zone, "holder@example.com")
        self.staff = t.make_staff("staff@example.com")
        self.routes = (
            ("/api/auth/login", "holder@example.com", "household"),
            ("/api/staff/auth/login", "staff@example.com", "staff"),
        )

    def post(self, client, path, email, password=t.PASSWORD, **extra):
        return client.post(path, json.dumps({"login_email": email, "password": password, **extra}),
                           content_type="application/json")

    def test_each_endpoint_accepts_its_role_and_rejects_other_credentials(self):
        for path, email, role in self.routes:
            with self.subTest(role=role):
                client = Client()
                wrong_email = "staff@example.com" if role == "household" else "holder@example.com"
                self.assertEqual(self.post(client, path, wrong_email).status_code, 401)
                self.assertEqual(client.get("/api/auth/me").status_code, 401)
                response = self.post(client, path, "  " + email.upper() + "  ", role="ignored")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["role"], role)

    def test_same_email_in_both_tables_never_falls_back(self):
        self.staff.login_email = self.holder.login_email
        self.staff.password_hash = make_password("staff-only-password")
        self.staff.save()
        for path, password, role, wrong_password in (
            ("/api/auth/login", t.PASSWORD, "household", "staff-only-password"),
            ("/api/staff/auth/login", "staff-only-password", "staff", t.PASSWORD),
        ):
            client = Client()
            self.assertEqual(self.post(client, path, self.holder.login_email, wrong_password).status_code, 401)
            response = self.post(client, path, self.holder.login_email, password)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["role"], role)

    def test_wrong_password_and_unknown_email(self):
        for path, email, _ in self.routes:
            for login_email, password in ((email, "wrong"), ("absent@example.com", t.PASSWORD)):
                self.assertEqual(self.post(self.client, path, login_email, password).status_code, 401)

    def test_malformed_credentials_and_non_post_requests(self):
        bodies = ["{", "[]", "null", "{}", '{"login_email":123,"password":"test"}',
                  '{"login_email":"staff@example.com","password":123}',
                  '{"login_email":"  ","password":"test"}']
        for path, _, _ in self.routes:
            self.assertEqual(self.client.get(path).status_code, 405)
            for body in bodies:
                with self.subTest(path=path, body=body):
                    self.assertEqual(self.client.post(path, body, content_type="application/json").status_code, 400)

    def test_cookie_restores_identity_and_shared_logout_clears_both_roles(self):
        for path, email, _ in self.routes:
            client = Client()
            user = self.post(client, path, email).json()
            refreshed = Client()
            refreshed.cookies = client.cookies.copy()
            self.assertEqual(refreshed.get("/api/auth/me").json(), user)
            for _ in range(2):
                self.assertEqual(refreshed.post("/api/auth/logout").status_code, 200)
            self.assertEqual(refreshed.get("/api/auth/me").status_code, 401)

    def test_successful_login_replaces_previous_role(self):
        for path, email, role in (*self.routes, self.routes[0]):
            self.assertEqual(self.post(self.client, path, email).status_code, 200)
            self.assertEqual(self.client.get("/api/auth/me").json()["role"], role)

    def test_staff_guard_checks_role_and_rechecks_deleted_account(self):
        # No staff feature route exists yet: exercise the real reusable guard directly.
        guarded = staff_required(lambda request: JsonResponse(request.current_user))

        def guarded_status(client):
            request = RequestFactory().get("/test-only")
            request.session = client.session
            return guarded(request).status_code

        self.assertEqual(guarded_status(self.client), 401)
        self.post(self.client, "/api/auth/login", "holder@example.com")
        self.assertEqual(guarded_status(self.client), 403)
        self.post(self.client, "/api/staff/auth/login", "staff@example.com")
        self.assertEqual(guarded_status(self.client), 200)
        self.assertEqual(self.client.get("/api/household").status_code, 403)
        self.assertEqual(self.client.get("/api/events").status_code, 200)
        self.assertEqual(self.client.get("/api/notices?scope=all").status_code, 200)
        self.staff.delete()
        self.assertEqual(guarded_status(self.client), 401)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_csrf_is_required_for_both_login_routes_and_shared_logout(self):
        for path, email, _ in self.routes:
            client = Client(enforce_csrf_checks=True)
            self.assertEqual(self.post(client, path, email).status_code, 403)
            self.assertEqual(client.get("/api/auth/csrf").status_code, 200)
            body = json.dumps({"login_email": email, "password": t.PASSWORD})
            self.assertEqual(client.post(path, body, content_type="application/json",
                                         HTTP_X_CSRFTOKEN="invalid").status_code, 403)
            response = client.post(path, body, content_type="application/json",
                                   HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(client.post("/api/auth/logout").status_code, 403)
            self.assertEqual(client.post("/api/auth/logout",
                                        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code, 200)
            self.assertEqual(client.get("/api/auth/me").status_code, 401)


class EventOverviewTests(TestCase):
    def setUp(self):
        import datetime

        self.zone_a = t.make_zone("Zone A")
        self.zone_b = t.make_zone("Zone B")
        t.make_household(self.zone_a)
        self.staff = t.make_staff()
        self.active = t.make_event("Active fire")
        self.closed = t.make_event("Closed fire", status="Closed")
        self.closed.end_date = datetime.date(2026, 8, 4)
        self.closed.save()
        self.old = t.make_notice(self.active, self.staff, [self.zone_a], "Older",
                                 datetime.datetime(2026, 8, 1, 12))
        self.new = t.make_notice(self.active, self.staff, [self.zone_b, self.zone_a], "Newer")
        self.tie = t.make_notice(self.active, self.staff, [self.zone_b], "Same time")
        self.login()

    def login(self, staff=True):
        path = "/api/staff/auth/login" if staff else "/api/auth/login"
        email = "staff@example.com" if staff else "holder@example.com"
        response = self.client.post(path, json.dumps({"login_email": email, "password": t.PASSWORD}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_complete_overview_deduplicates_targets_and_orders_notices(self):
        response = self.client.get("/api/staff/events")
        self.assertEqual(response.status_code, 200)
        events = response.json()["events"]
        self.assertEqual([e["event_id"] for e in events], [self.closed.pk, self.active.pk])
        self.assertEqual(events[0]["notices"], [])
        self.assertEqual(events[0]["end_date"], "2026-08-04")
        active = events[1]
        self.assertEqual({k: v for k, v in active.items() if k != "notices"}, {
            "event_id": self.active.pk, "name": "Active fire", "event_type": "Wildfire",
            "status": "Active", "start_date": "2026-08-01", "end_date": None,
        })
        self.assertEqual([n["notice_id"] for n in active["notices"]], [self.tie.pk, self.new.pk, self.old.pk])
        notice = active["notices"][1]
        self.assertEqual(notice, {
            "notice_id": self.new.pk, "title": "Newer", "message": "Message text",
            "published_at": self.new.published_at.isoformat(),
            "event": {k: v for k, v in active.items() if k != "notices"},
            "publisher": {"staff_id": self.staff.pk, "name": self.staff.name},
            "zones": [{"zone_id": self.zone_a.pk, "zone_name": "Zone A"},
                      {"zone_id": self.zone_b.pk, "zone_name": "Zone B"}],
        })

    def test_status_filters_and_invalid_values(self):
        for status, event in (("Active", self.active), ("Closed", self.closed)):
            response = self.client.get("/api/staff/events", {"status": status})
            self.assertEqual(response.status_code, 200)
            self.assertEqual([e["event_id"] for e in response.json()["events"]], [event.pk])
        for status in ("Pending", "active", "", "1"):
            self.assertEqual(self.client.get("/api/staff/events", {"status": status}).status_code, 400)

    def test_empty_filter_and_empty_database(self):
        self.closed.delete()
        self.assertEqual(self.client.get("/api/staff/events?status=Closed").json(), {"events": []})
        from core.models import EvacuationNotice, NoticeZone
        NoticeZone.objects.all().delete()
        EvacuationNotice.objects.all().delete()
        self.active.delete()
        self.assertEqual(self.client.get("/api/staff/events").json(), {"events": []})

    def test_overview_access_control_and_unsupported_method(self):
        self.assertEqual(self.client.delete("/api/staff/events").status_code, 405)
        self.client.post("/api/auth/logout")
        self.assertEqual(self.client.get("/api/staff/events").status_code, 401)
        self.login(staff=False)
        self.assertEqual(self.client.get("/api/staff/events").status_code, 403)

    def test_household_reads_keep_existing_shape_and_zone_selection(self):
        self.login(staff=False)
        events = self.client.get("/api/events").json()["events"]
        self.assertEqual(len(events), 2)
        self.assertNotIn("notices", events[0])
        notices = self.client.get("/api/notices").json()["notices"]
        self.assertEqual([n["notice_id"] for n in notices], [self.new.pk, self.old.pk])
        self.assertTrue(notices[0]["targets_my_zone"])
        self.assertEqual(notices[0]["published_at"], "2026-08-02 12:00")
        self.assertEqual(len(self.client.get("/api/zones").json()["zones"]), 2)


class EventWriteTests(TestCase):
    def setUp(self):
        self.zone = t.make_zone()
        self.household, self.member, _ = t.make_household(self.zone)
        self.staff = t.make_staff()
        response = self.client.post("/api/staff/auth/login", json.dumps({
            "login_email": "staff@example.com", "password": t.PASSWORD}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.data = {"name": "Flood warning", "event_type": "Flood", "start_date": "2026-08-01"}
        self.event = t.make_event()
        self.url = f"/api/staff/events/{self.event.pk}"

    def write(self, data, patch=False, client=None, **headers):
        client = client or self.client
        method = client.patch if patch else client.post
        return method(self.url if patch else "/api/staff/events", json.dumps(data),
                      content_type="application/json", **headers)

    def test_create_defaults_and_maximum_length_name(self):
        response = self.write({**self.data, "name": "N" * 100})
        self.assertEqual(response.status_code, 201)
        created = response.json()
        self.assertEqual(created, {**self.data, "name": "N" * 100, "event_id": created["event_id"],
                                   "status": "Active", "end_date": None})
        shared = self.client.get("/api/events").json()["events"]
        self.assertIn(created, shared)
        self.assertEqual(self.write({**self.data, "status": "Closed", "end_date": "2026-08-01"}).status_code, 201)

    def test_patch_merged_dates_clear_end_and_preserve_omitted_fields(self):
        self.assertEqual(self.write({"end_date": "2026-08-04"}, patch=True).status_code, 200)
        response = self.write({"name": "  Renamed  ", "start_date": "2026-08-05"}, patch=True)
        self.assertEqual(response.status_code, 400)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Test Wildfire")
        self.assertEqual(self.write({"end_date": "2026-07-31"}, patch=True).status_code, 400)
        response = self.write({"name": "  Renamed  ", "start_date": "2026-08-05", "end_date": None}, patch=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Renamed")
        self.assertIsNone(response.json()["end_date"])
        self.assertEqual(response.json()["event_type"], "Wildfire")
        self.assertEqual(self.write({}, patch=True).json(), response.json())

    def test_invalid_input_saves_nothing(self):
        from core.models import EmergencyEvent
        invalid = [
            {"name": " "}, {"name": "x" * 101}, {"name": 5},
            {"event_type": "Earthquake"}, {"event_type": []}, {"status": "Pending"},
            {"status": None}, {"start_date": None}, {"start_date": "2026-02-30"},
            {"start_date": "20260801"}, {"start_date": True}, {"end_date": ""},
            {"end_date": "2026-07-31"}, {"end_date": {}},
        ]
        before = EmergencyEvent.objects.count()
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assertEqual(self.write({**self.data, **changes}).status_code, 400)
                self.assertEqual(self.write(changes, patch=True).status_code, 400)
        self.assertEqual(self.write({}).status_code, 400)
        self.assertEqual(EmergencyEvent.objects.count(), before)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Test Wildfire")
        self.assertEqual(self.event.status, "Active")
        for method, url in ((self.client.post, "/api/staff/events"), (self.client.patch, self.url)):
            for body in ("{", "[]", "null"):
                self.assertEqual(method(url, body, content_type="application/json").status_code, 400)

    def test_access_control_missing_event_and_no_delete(self):
        self.assertEqual(self.client.patch("/api/staff/events/999999", "{}", content_type="application/json").status_code, 404)
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        anonymous = Client()
        for patch in (False, True):
            self.assertEqual(self.write(self.data, patch=patch, client=anonymous).status_code, 401)
        anonymous.post("/api/auth/login", json.dumps({"login_email": "holder@example.com", "password": t.PASSWORD}),
                       content_type="application/json")
        for patch in (False, True):
            self.assertEqual(self.write(self.data, patch=patch, client=anonymous).status_code, 403)

    def test_writes_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.cookies = self.client.cookies.copy()
        for patch in (False, True):
            self.assertEqual(self.write(self.data, patch=patch, client=client).status_code, 403)
        client.get("/api/auth/csrf")
        token = client.cookies["csrftoken"].value
        self.assertEqual(self.write(self.data, client=client, HTTP_X_CSRFTOKEN=token).status_code, 201)
        self.assertEqual(self.write({"status": "Closed"}, patch=True, client=client, HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_closing_event_preserves_stays_and_updates_shared_reads(self):
        from django.db import connection
        notice = t.make_notice(self.event, self.staff, [self.zone])
        with connection.cursor() as cur:
            cur.execute("INSERT INTO REGISTRATION (household_id,event_id,submitter_id) VALUES (%s,%s,%s)",
                        [self.household.pk, self.event.pk, self.member.pk])
            registration_id = cur.lastrowid
            cur.execute("INSERT INTO REGISTRATION_MEMBER VALUES (%s,%s)", [registration_id, self.member.pk])
            cur.execute("INSERT INTO SHELTER (name,address,capacity,available_spaces) VALUES ('Test','Test',10,9)")
            shelter_id = cur.lastrowid
            cur.execute("INSERT INTO MANAGES VALUES (%s,%s)", [self.staff.pk, shelter_id])
            cur.execute("INSERT INTO PLACEMENT (registration_id,placement_no,shelter_id) VALUES (%s,1,%s)",
                        [registration_id, shelter_id])

        def snapshot():
            with connection.cursor() as cur:
                result = []
                for table in ("REGISTRATION", "REGISTRATION_MEMBER", "PLACEMENT", "SHELTER", "MANAGES"):
                    cur.execute("SELECT * FROM " + connection.ops.quote_name(table))
                    result.append(cur.fetchall())
                return result

        # Closing preserves both reserved and already-arrived stays.
        for status in ("Reserved", "Arrived"):
            with connection.cursor() as cur:
                cur.execute("UPDATE PLACEMENT SET status=%s, arrival_time=%s WHERE registration_id=%s",
                            [status, "2026-08-02 12:00:00" if status == "Arrived" else None, registration_id])
            self.write({"status": "Active"}, patch=True)
            before = snapshot()
            response = self.write({"status": "Closed"}, patch=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(snapshot(), before)
        detail = self.client.get(f"/api/notices/{notice.pk}").json()
        self.assertEqual(detail["event"]["status"], "Closed")
        self.assertFalse(detail["can_register"])
        events = self.client.get("/api/events").json()["events"]
        self.assertEqual(events[0]["status"], "Closed")


class NoticeWriteTests(TestCase):
    def setUp(self):
        self.zone = t.make_zone('Zone A')
        self.other = t.make_zone('Zone B')
        t.make_household(self.zone)
        self.staff = t.make_staff()
        self.event = t.make_event(status='Closed')
        self.notice = t.make_notice(self.event, self.staff, [self.zone])
        self.url = f'/api/staff/notices/{self.notice.pk}'
        self.client.post('/api/staff/auth/login', json.dumps({
            'login_email': self.staff.login_email, 'password': t.PASSWORD}), content_type='application/json')
        self.data = {'event_id': self.event.pk, 'title': ' Evacuate ', 'message': ' Leave now ',
                     'zone_ids': [self.other.pk, self.zone.pk, self.zone.pk]}

    def write(self, data, editing=False, client=None, **headers):
        client = client or self.client
        return (client.patch if editing else client.post)(
            self.url if editing else '/api/staff/notices', json.dumps(data),
            content_type='application/json', **headers)

    def snapshot(self):
        from core.models import EvacuationNotice, NoticeZone
        return (list(EvacuationNotice.objects.values()), list(NoticeZone.objects.values()))

    def test_create_and_edit_contract_metadata_and_targets(self):
        from django.utils import timezone
        from core.models import EvacuationNotice
        before = timezone.now().replace(microsecond=0)
        response = self.write({**self.data, 'title': 'x' * 150, 'staff_id': 999999,
                               'published_at': '2000-01-01'})
        self.assertEqual(response.status_code, 201)
        row = response.json()
        self.assertEqual(row['title'], 'x' * 150)
        self.assertEqual(row['message'], 'Leave now')
        self.assertEqual(row['publisher'], {'staff_id': self.staff.pk, 'name': self.staff.name})
        self.assertEqual(row['event']['status'], 'Closed')
        self.assertEqual([z['zone_id'] for z in row['zones']], [self.zone.pk, self.other.pk])
        saved = EvacuationNotice.objects.get(pk=row['notice_id'])
        self.assertGreaterEqual(saved.published_at, before)
        self.assertLessEqual(saved.published_at, timezone.now())
        self.assertIn(row, self.client.get('/api/staff/events').json()['events'][0]['notices'])
        editor = t.make_staff('editor@example.com')
        self.client.post('/api/staff/auth/login', json.dumps({
            'login_email': editor.login_email, 'password': t.PASSWORD}), content_type='application/json')
        response = self.write({'title': ' Corrected ', 'event_id': t.make_event().pk,
                               'staff_id': editor.pk, 'published_at': '2000-01-01'}, editing=True)
        self.assertEqual(response.status_code, 200)
        row = response.json()
        self.assertEqual(row['title'], 'Corrected')
        self.assertEqual(row['message'], 'Message text')
        self.assertEqual(row['event']['event_id'], self.event.pk)
        self.assertEqual(row['publisher']['staff_id'], self.staff.pk)
        self.assertEqual(row['published_at'], self.notice.published_at.isoformat())
        self.assertEqual([z['zone_id'] for z in row['zones']], [self.zone.pk])
        self.assertEqual(self.write({}, editing=True).json(), row)
        response = self.write({'zone_ids': [self.other.pk, self.other.pk]}, editing=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([z['zone_id'] for z in response.json()['zones']], [self.other.pk])

    def test_invalid_inputs_save_nothing(self):
        before = self.snapshot()
        invalid = [{'title': ' '}, {'title': 'x' * 151}, {'title': 1}, {'message': None},
                   {'message': ' '}, {'zone_ids': []}, {'zone_ids': None}, {'zone_ids': '1'},
                   {'zone_ids': [True]}, {'zone_ids': [1.0]}, {'zone_ids': [{}]},
                   {'zone_ids': [-1]}, {'zone_ids': [self.zone.pk, 999999]}]
        for change in invalid:
            with self.subTest(change=change):
                self.assertEqual(self.write({**self.data, **change}).status_code, 400)
                self.assertEqual(self.write({'title': 'Must not save', **change}, editing=True).status_code, 400)
        for event_id in (None, True, '1', -1, 999999):
            self.assertEqual(self.write({**self.data, 'event_id': event_id}).status_code, 400)
        self.assertEqual(self.write({}).status_code, 400)
        for method, url in ((self.client.post, '/api/staff/notices'), (self.client.patch, self.url)):
            for body in ('{', '[]', 'null'):
                self.assertEqual(method(url, body, content_type='application/json').status_code, 400)
        self.assertEqual(self.snapshot(), before)

    def test_related_write_failure_rolls_back(self):
        from unittest.mock import patch
        from django.db import IntegrityError
        before = self.snapshot()
        for editing in (False, True):
            with patch('staff.views.NoticeZone.objects.bulk_create', side_effect=IntegrityError('test failure')):
                with self.assertRaises(IntegrityError):
                    self.write(self.data, editing=editing)
            self.assertEqual(self.snapshot(), before)

    def test_household_visibility_tracks_changes(self):
        household = Client()
        household.post('/api/auth/login', json.dumps({'login_email': 'holder@example.com',
                                                     'password': t.PASSWORD}), content_type='application/json')
        created = self.write(self.data).json()
        rows = household.get('/api/notices').json()['notices']
        self.assertIn(created['notice_id'], [r['notice_id'] for r in rows])
        self.write({'title': 'Updated', 'zone_ids': [self.other.pk]}, editing=True)
        rows = household.get('/api/notices').json()['notices']
        self.assertNotIn(self.notice.pk, [r['notice_id'] for r in rows])
        detail = household.get(f'/api/notices/{self.notice.pk}').json()
        self.assertEqual(detail['title'], 'Updated')
        self.assertFalse(detail['targets_my_zone'])
        self.assertEqual([z['zone_id'] for z in detail['zones']], [self.other.pk])

    def test_access_and_csrf(self):
        self.assertEqual(self.client.patch('/api/staff/notices/999999', '{}', content_type='application/json').status_code, 404)
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        self.assertEqual(self.client.get('/api/staff/notices').status_code, 405)
        client = Client()
        for editing in (False, True):
            self.assertEqual(self.write(self.data, editing=editing, client=client).status_code, 401)
        client.post('/api/auth/login', json.dumps({'login_email': 'holder@example.com',
                                                 'password': t.PASSWORD}), content_type='application/json')
        for editing in (False, True):
            self.assertEqual(self.write(self.data, editing=editing, client=client).status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.cookies = self.client.cookies.copy()
        for editing in (False, True):
            self.assertEqual(self.write(self.data, editing=editing, client=client).status_code, 403)
        client.get('/api/auth/csrf')
        token = client.cookies['csrftoken'].value
        self.assertEqual(self.write(self.data, client=client, HTTP_X_CSRFTOKEN=token).status_code, 201)
        self.assertEqual(self.write({'message': 'Correction'}, editing=True, client=client,
                                    HTTP_X_CSRFTOKEN=token).status_code, 200)
