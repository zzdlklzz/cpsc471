import json

from django.db import connection
from django.test import TestCase

from core import testing as t
from core.models import AccountHolder, Household, HouseholdMember


class Base(TestCase):
    def setUp(self):
        self.zone = t.make_zone("Zone A")
        self.zone_b = t.make_zone("Zone B")
        self.household, self.member, self.account = t.make_household(self.zone, "anh@example.com")
        self.staff = t.make_staff("staff@example.com")

    def post(self, url, data):
        return self.client.post(url, json.dumps(data), content_type="application/json")

    def patch(self, url, data):
        return self.client.patch(url, json.dumps(data), content_type="application/json")

    def login(self, email="anh@example.com", url="/api/auth/login"):
        response = self.post(url, {"login_email": email, "password": t.PASSWORD})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def signup_data(self, **changes):
        data = {"street": "5 New St", "city": "Calgary", "province": "Alberta", "postal_code": "T2N 1N4",
                "zone_id": self.zone.zone_id, "first_name": "Mia", "last_name": "Cruz",
                "date_of_birth": "1995-04-03", "phone_number": "", "login_email": "mia@example.com",
                "password": "long-enough-pw"}
        data.update(changes)
        return data


class AuthTests(Base):
    def test_household_login_returns_role_and_ids(self):
        user = self.login()
        self.assertEqual(user["role"], "household")
        self.assertEqual(user["member_id"], self.member.member_id)
        self.assertEqual(user["household_id"], self.household.household_id)

    def test_staff_login_returns_staff_role(self):
        user = self.login("staff@example.com", url="/api/staff/auth/login")
        self.assertEqual(user["role"], "staff")
        self.assertEqual(user["staff_id"], self.staff.staff_id)
        self.assertIsNone(user["household_id"])

    def test_wrong_password_is_rejected(self):
        r = self.post("/api/auth/login", {"login_email": "anh@example.com", "password": "wrong"})
        self.assertEqual(r.status_code, 401)

    def test_me_requires_login_and_logout_ends_session(self):
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.login()
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.post("/api/auth/logout", {})
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_password_is_stored_hashed(self):
        self.assertNotIn(t.PASSWORD, self.account.password_hash)


class SignupTests(Base):
    def test_signup_creates_household_member_and_account_and_logs_in(self):
        r = self.post("/api/auth/signup", self.signup_data())
        self.assertEqual(r.status_code, 201, r.content)
        user = r.json()
        self.assertEqual(user["role"], "household")
        member = HouseholdMember.objects.get(pk=user["member_id"])
        self.assertEqual(member.household.street, "5 New St")
        self.assertTrue(AccountHolder.objects.filter(pk=member.member_id).exists())
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_signup_rejects_missing_fields_and_saves_nothing(self):
        before = Household.objects.count()
        r = self.post("/api/auth/signup", self.signup_data(first_name="", password="short"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("first_name", r.json()["fields"])
        self.assertIn("password", r.json()["fields"])
        self.assertEqual(Household.objects.count(), before)

    def test_signup_rejects_existing_household_email_and_staff_email(self):
        for email in ("anh@example.com", "staff@example.com"):
            r = self.post("/api/auth/signup", self.signup_data(login_email=email))
            self.assertEqual(r.status_code, 400)
            self.assertIn("login_email", r.json()["fields"])

    def test_signup_rejects_unknown_zone(self):
        r = self.post("/api/auth/signup", self.signup_data(zone_id=99999))
        self.assertEqual(r.status_code, 400)
        self.assertIn("zone_id", r.json()["fields"])

    def test_zones_are_public(self):
        r = self.client.get("/api/zones")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["zones"]), 2)


class HouseholdTests(Base):
    def setUp(self):
        super().setUp()
        self.other_household, self.other_member, _ = t.make_household(self.zone_b, "other@example.com", "Omar", "Haddad")

    def test_household_requires_login(self):
        self.assertEqual(self.client.get("/api/household").status_code, 401)

    def test_staff_cannot_open_household_pages(self):
        self.login("staff@example.com", url="/api/staff/auth/login")
        self.assertEqual(self.client.get("/api/household").status_code, 403)

    def test_get_shows_only_own_household(self):
        self.login()
        data = self.client.get("/api/household").json()
        self.assertEqual(data["household_id"], self.household.household_id)
        self.assertEqual([m["member_id"] for m in data["members"]], [self.member.member_id])
        self.assertTrue(data["members"][0]["is_account_holder"])

    def test_update_address_and_zone(self):
        self.login()
        r = self.patch("/api/household", {"street": "9 Moved Ave", "zone_id": self.zone_b.zone_id})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["street"], "9 Moved Ave")
        self.assertEqual(r.json()["zone"]["zone_id"], self.zone_b.zone_id)

    def test_update_rejects_unknown_zone(self):
        self.login()
        self.assertEqual(self.patch("/api/household", {"zone_id": 99999}).status_code, 400)

    def test_add_and_edit_member(self):
        self.login()
        r = self.post("/api/household/members", {"first_name": "Linh", "last_name": "Nguyen", "date_of_birth": "2010-02-02"})
        self.assertEqual(r.status_code, 201, r.content)
        new_id = [m for m in r.json()["members"] if m["first_name"] == "Linh"][0]["member_id"]
        r = self.patch(f"/api/household/members/{new_id}", {"phone_number": "403-555-0100"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(HouseholdMember.objects.get(pk=new_id).phone_number, "403-555-0100")

    def test_cannot_edit_or_remove_member_of_another_household(self):
        self.login()
        url = f"/api/household/members/{self.other_member.member_id}"
        self.assertEqual(self.patch(url, {"first_name": "Hacked"}).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(HouseholdMember.objects.get(pk=self.other_member.member_id).first_name, "Omar")

    def test_remove_unreferenced_member(self):
        extra = t.make_member(self.household, "Minh")
        self.login()
        r = self.client.delete(f"/api/household/members/{extra.member_id}")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertFalse(HouseholdMember.objects.filter(pk=extra.member_id).exists())

    def test_cannot_remove_member_used_by_a_registration(self):
        extra = t.make_member(self.household, "Minh")
        event = t.make_event()
        with connection.cursor() as cur:
            cur.execute("INSERT INTO REGISTRATION (submitted_at, status, household_id, event_id, submitter_id)"
                        " VALUES ('2026-08-02 10:00:00', 'Active', %s, %s, %s)",
                        [self.household.household_id, event.event_id, self.member.member_id])
            cur.execute("INSERT INTO REGISTRATION_MEMBER (registration_id, member_id) VALUES (LAST_INSERT_ID(), %s)",
                        [extra.member_id])
        self.login()
        r = self.client.delete(f"/api/household/members/{extra.member_id}")
        self.assertEqual(r.status_code, 409)
        self.assertTrue(HouseholdMember.objects.filter(pk=extra.member_id).exists())

    def test_cannot_remove_yourself(self):
        self.login()
        r = self.client.delete(f"/api/household/members/{self.member.member_id}")
        self.assertEqual(r.status_code, 409)

    def test_enable_account_lets_second_member_log_in_and_then_be_removed(self):
        extra = t.make_member(self.household, "Linh")
        self.login()
        url = f"/api/household/members/{extra.member_id}/account"
        r = self.post(url, {"login_email": "linh@example.com", "password": t.PASSWORD})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(self.post(url, {"login_email": "x@example.com", "password": t.PASSWORD}).status_code, 409)
        # two holders now, so the second one may be removed by the first
        self.assertEqual(self.client.delete(f"/api/household/members/{extra.member_id}").status_code, 200)

    def test_enable_account_rejects_used_email(self):
        extra = t.make_member(self.household, "Linh")
        self.login()
        r = self.post(f"/api/household/members/{extra.member_id}/account",
                      {"login_email": "staff@example.com", "password": t.PASSWORD})
        self.assertEqual(r.status_code, 400)
