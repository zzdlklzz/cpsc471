"""Shared login and access-check helpers. Persons 2 and 3 import these.

Usage in a view:

    from core.auth_helpers import household_required, staff_required

    @household_required
    def my_view(request):
        user = request.current_user      # {"role", "member_id", "staff_id", "household_id", ...}
"""
import json
from functools import wraps

from django.http import JsonResponse

from .models import AccountHolder, Staff

SESSION_KEY = "evac_user"


def api_error(status, message, fields=None):
    """Every error response has the same shape: {"error": "...", "fields": {...}}."""
    body = {"error": message}
    if fields:
        body["fields"] = fields
    return JsonResponse(body, status=status)


def read_json(request):
    """Return the JSON body as a dict, or None if it is not valid JSON."""
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def set_current_user(request, user):
    request.session.flush()
    request.session[SESSION_KEY] = user


def clear_current_user(request):
    request.session.flush()


def get_current_user(request):
    """Return the logged-in user as a dict, or None.

    The account is looked up again on every request, so a removed account
    cannot keep using an old session cookie.
    """
    data = request.session.get(SESSION_KEY)
    if not data:
        return None
    if data.get("role") == "staff":
        staff = Staff.objects.filter(pk=data.get("staff_id")).first()
        if staff is None:
            return None
        return {"role": "staff", "staff_id": staff.staff_id, "member_id": None, "household_id": None,
                "name": staff.name, "email": staff.login_email}
    holder = AccountHolder.objects.select_related("member").filter(pk=data.get("member_id")).first()
    if holder is None:
        return None
    member = holder.member
    return {"role": "household", "staff_id": None, "member_id": member.member_id,
            "household_id": member.household_id,
            "name": f"{member.first_name} {member.last_name}", "email": holder.login_email}


def _guard(role):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = get_current_user(request)
            if user is None:
                return api_error(401, "Please log in.")
            if role and user["role"] != role:
                return api_error(403, "You do not have access to this page.")
            request.current_user = user
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


login_required_api = _guard(None)          # any logged-in user
household_required = _guard("household")   # account holders only
staff_required = _guard("staff")           # staff only
