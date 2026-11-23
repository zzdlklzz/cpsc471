from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test.runner import DiscoverRunner


class SchemaTestRunner(DiscoverRunner):
    """Load the table-only v2 schema into Django's isolated MySQL test database."""

    def setup_databases(self, **kwargs):
        development_name = connection.settings_dict["NAME"]
        test_name = connection.creation._get_test_db_name()
        if connection.vendor != "mysql" or test_name.casefold() == development_name.casefold():
            raise ImproperlyConfigured("Tests require a separate MySQL test database.")
        config = super().setup_databases(**kwargs)
        # A test selection with no database tests can skip database creation.
        if connection.settings_dict["NAME"] == development_name:
            return config
        sql = (settings.BASE_DIR / "sql" / "schema-v2.sql").read_text(encoding="utf-8")
        lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
        statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
        with connection.cursor() as cur:
            for statement in statements:
                if statement.upper().startswith(("DROP DATABASE", "CREATE DATABASE", "USE ")):
                    continue
                cur.execute(statement)
        return config
