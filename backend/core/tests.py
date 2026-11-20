from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import SimpleTestCase, TestCase

from .test_runner import SchemaTestRunner
from .models import EmergencyEvent, EvacuationNotice, Staff
from .testing import make_event, make_notice, make_staff


class TestRunnerSafetyTests(SimpleTestCase):
    def test_development_database_cannot_be_used_as_test_database(self):
        with patch.object(connection.creation, "_get_test_db_name",
                          return_value=connection.settings_dict["NAME"].swapcase()), \
                patch("django.test.runner.DiscoverRunner.setup_databases") as setup:
            with self.assertRaisesMessage(ImproperlyConfigured, "separate MySQL"):
                SchemaTestRunner().setup_databases()
            setup.assert_not_called()


class SchemaV2Tests(TestCase):
    def test_event_columns_use_v2_lengths(self):
        with connection.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM EMERGENCY_EVENT")
            columns = {row[0]: row[1] for row in cursor.fetchall()}
        self.assertEqual(columns["name"], "varchar(100)")
        self.assertEqual(columns["event_type"], "varchar(20)")

    def test_invalid_event_status_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_event(status="Pending")


class StaffMappingTests(TestCase):
    def test_field_lengths_match_mysql_columns(self):
        for model, names in (
            (Staff, ("name", "login_email")),
            (EmergencyEvent, ("name", "event_type", "status")),
            (EvacuationNotice, ("title",)),
        ):
            with connection.cursor() as cursor:
                cursor.execute("SHOW COLUMNS FROM " + connection.ops.quote_name(model._meta.db_table))
                columns = {row[0]: row[1] for row in cursor.fetchall()}
            for name in names:
                with self.subTest(model=model.__name__, field=name):
                    field = model._meta.get_field(name)
                    self.assertEqual(columns[name], f"varchar({field.max_length})")

    def test_length_validation_accepts_limit_and_rejects_one_over(self):
        for model, name, limit in (
            (Staff, "name", 100), (Staff, "login_email", 100),
            (EmergencyEvent, "name", 100), (EmergencyEvent, "event_type", 20),
            (EmergencyEvent, "status", 20), (EvacuationNotice, "title", 150),
        ):
            with self.subTest(model=model.__name__, field=name):
                instance = model(**{name: "x" * limit})
                exclude = [field.name for field in model._meta.fields if field.name != name]
                # Check lengths independently of other fields and database enum checks.
                instance.clean_fields(exclude=exclude)
                setattr(instance, name, "x" * (limit + 1))
                with self.assertRaises(ValidationError) as raised:
                    instance.clean_fields(exclude=exclude)
                self.assertEqual(raised.exception.error_dict[name][0].code, "max_length")

    def test_maximum_length_text_round_trips_without_truncation(self):
        staff = make_staff("s" * 88 + "@example.com")
        staff.name = "s" * 100
        staff.full_clean()
        staff.save()
        event = make_event("e" * 100)
        notice = make_notice(event, staff, [], title="n" * 150)
        for instance, fields in (
            (staff, ("name", "login_email")), (event, ("name",)), (notice, ("title",)),
        ):
            expected = {name: getattr(instance, name) for name in fields}
            instance.refresh_from_db()
            for name, value in expected.items():
                self.assertEqual(getattr(instance, name), value)
