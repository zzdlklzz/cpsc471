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
