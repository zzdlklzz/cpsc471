from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.auth_helpers import api_error, get_current_user, read_json, set_current_user, staff_required
from core.models import Staff

from .queries import event_overview


@require_http_methods(["POST"])
def login(request):
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    email = data.get("login_email")
    email = email.strip().lower() if isinstance(email, str) else ""
    password = data.get("password")
    if not email or not isinstance(password, str) or not password:
        return api_error(400, "Enter your email and password.")

    staff = Staff.objects.filter(login_email__iexact=email).first()
    if staff is not None and check_password(password, staff.password_hash):
        set_current_user(request, {"role": "staff", "staff_id": staff.staff_id})
        return JsonResponse(get_current_user(request))
    return api_error(401, "The email or password is not correct.")


@staff_required
@require_http_methods(["GET"])
def events(request):
    status = request.GET.get("status")
    if status is not None and status not in ("Active", "Closed"):
        return api_error(400, "Choose Active or Closed for status.")
    return JsonResponse({"events": event_overview(status)})
