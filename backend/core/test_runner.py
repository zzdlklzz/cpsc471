from django.conf import settings
from django.db import connection
from django.test.runner import DiscoverRunner


class SchemaTestRunner(DiscoverRunner):
    """Creates our tables in the test database by running backend/sql/schema-v1.sql."""

    def setup_databases(self, **kwargs):
        config = super().setup_databases(**kwargs)
        sql = (settings.BASE_DIR / "sql" / "schema-v1.sql").read_text(encoding="utf-8")
        lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
        statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
        with connection.cursor() as cur:
            for statement in statements:
                if statement.upper().startswith(("DROP DATABASE", "CREATE DATABASE", "USE ")):
                    continue
                cur.execute(statement)
        return config
