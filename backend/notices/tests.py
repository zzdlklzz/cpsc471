import datetime
import json

from django.test import TestCase

from core import testing as t


class NoticeTests(TestCase):
    def setUp(self):
        self.zone_a, self.zone_b = t.make_zone("Zone A"), t.make_zone("Zone B")
        t.make_household(self.zone_a, "anh@example.com")
        self.staff = t.make_staff()
        self.fire = t.make_event("Fire", "Active")
        self.flood = t.make_event("Flood", "Closed")
        self.n_old = t.make_notice(self.fire, self.staff, [self.zone_a], "Old A", datetime.datetime(2026, 8, 1, 9, 0))
        self.n_new = t.make_notice(self.fire, self.staff, [self.zone_a, self.zone_b], "New A and B", datetime.datetime(2026, 8, 3, 9, 0))
        self.n_b = t.make_notice(self.fire, self.staff, [self.zone_b], "Only B", datetime.datetime(2026, 8, 2, 9, 0))
        self.n_flood = t.make_notice(self.flood, self.staff, [self.zone_a], "Flood A", datetime.datetime(2026, 4, 1, 9, 0))

    def login(self, email="anh@example.com"):
        r = self.client.post("/api/auth/login", json.dumps({"login_email": email, "password": t.PASSWORD}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)

    def ids(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, r.content)
        return [n["notice_id"] for n in r.json()["notices"]]

    def test_notices_require_login(self):
        self.assertEqual(self.client.get("/api/notices").status_code, 401)

    def test_default_shows_home_zone_notices_newest_first(self):
        self.login()
        self.assertEqual(self.ids("/api/notices"),
                         [self.n_new.notice_id, self.n_old.notice_id, self.n_flood.notice_id])

    def test_scope_all_includes_other_zones(self):
        self.login()
        self.assertIn(self.n_b.notice_id, self.ids("/api/notices?scope=all"))

    def test_filter_by_event_and_by_zone(self):
        self.login()
        self.assertEqual(self.ids(f"/api/notices?event={self.flood.event_id}"), [self.n_flood.notice_id])
        self.assertEqual(self.ids(f"/api/notices?zone={self.zone_b.zone_id}"),
                         [self.n_new.notice_id, self.n_b.notice_id])

    def test_bad_filter_is_rejected(self):
        self.login()
        self.assertEqual(self.client.get("/api/notices?event=abc").status_code, 400)

    def test_detail_shows_event_zones_and_register_flag(self):
        self.login()
        data = self.client.get(f"/api/notices/{self.n_new.notice_id}").json()
        self.assertEqual(data["title"], "New A and B")
        self.assertEqual([z["zone_name"] for z in data["zones"]], ["Zone A", "Zone B"])
        self.assertTrue(data["targets_my_zone"])
        self.assertTrue(data["can_register"])
        closed = self.client.get(f"/api/notices/{self.n_flood.notice_id}").json()
        self.assertFalse(closed["can_register"])

    def test_unknown_notice_is_404(self):
        self.login()
        self.assertEqual(self.client.get("/api/notices/99999").status_code, 404)

    def test_events_list(self):
        self.login()
        self.assertEqual(len(self.client.get("/api/events").json()["events"]), 2)
