from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, connection, transaction
from django.test import SimpleTestCase, TestCase

from .test_runner import SchemaTestRunner
from .testing import make_event


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
