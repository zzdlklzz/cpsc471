from django.db import connection
from django.http import JsonResponse


def health(request):
    """Development check: proves Django can reach MySQL and see our schema."""
    with connection.cursor() as cur:
        cur.execute("SELECT DATABASE()")
        db_name = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
        table_count = cur.fetchone()[0]
    return JsonResponse({"status": "ok", "database": db_name, "tables": table_count})
