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

    def test_access_control_and_read_only_route(self):
        self.assertEqual(self.client.post("/api/staff/events").status_code, 405)
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
