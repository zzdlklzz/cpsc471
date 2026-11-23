from django.contrib.auth.hashers import check_password, make_password
from django.db import connection, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from core.auth_helpers import (api_error, clear_current_user, get_current_user,
                               household_required, read_json, set_current_user)
from core.models import AccountHolder, EvacuationZone, Household, HouseholdMember, Staff

from . import serializers


# ------------------------------------------------------------------ helpers
def _email_in_use(email):
    return (AccountHolder.objects.filter(login_email__iexact=email).exists()
            or Staff.objects.filter(login_email__iexact=email).exists())


def _household_response(household_id, status=200):
    household = Household.objects.select_related("zone").get(pk=household_id)
    members = list(HouseholdMember.objects.filter(household_id=household_id)
                   .order_by("member_id"))
    accounts = AccountHolder.objects.filter(member__household_id=household_id)
    emails = {a.member_id: a.login_email for a in accounts}
    return JsonResponse(serializers.household_to_dict(household, members, emails), status=status)


def _member_is_referenced(member_id):
    """True if the member takes part in a registration or submitted one."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM REGISTRATION_MEMBER WHERE member_id = %s)"
            " OR EXISTS(SELECT 1 FROM REGISTRATION WHERE submitter_id = %s)",
            [member_id, member_id])
        return bool(cur.fetchone()[0])


# ------------------------------------------------------------------ auth
@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf(request):
    """The React app calls this once at start-up to receive the CSRF cookie."""
    return JsonResponse({"detail": "CSRF cookie set."})


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

    holder = AccountHolder.objects.filter(login_email__iexact=email).first()
    if holder is not None and check_password(password, holder.password_hash):
        set_current_user(request, {"role": "household", "member_id": holder.member_id})
        return JsonResponse(get_current_user(request))
    return api_error(401, "The email or password is not correct.")


@require_http_methods(["POST"])
def logout(request):
    clear_current_user(request)
    return JsonResponse({"detail": "Logged out."})


@require_http_methods(["GET"])
def me(request):
    user = get_current_user(request)
    if user is None:
        return api_error(401, "Please log in.")
    return JsonResponse(user)


@require_http_methods(["GET"])
def zones(request):
    """Predefined zones. Public, because the sign-up form needs them."""
    rows = EvacuationZone.objects.order_by("zone_name")
    return JsonResponse({"zones": [{"zone_id": z.zone_id, "zone_name": z.zone_name} for z in rows]})


@require_http_methods(["POST"])
def signup(request):
    """Creates the household, its first member and the login together. Never creates staff."""
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    household, e1 = serializers.validate_household(data)
    member, e2 = serializers.validate_member(data)
    creds, e3 = serializers.validate_credentials(data)
    errors = {**e1, **e2, **e3}
    if "zone_id" in household and not EvacuationZone.objects.filter(pk=household["zone_id"]).exists():
        errors["zone_id"] = "Choose an evacuation zone from the list."
    if "login_email" in creds and _email_in_use(creds["login_email"]):
        errors["login_email"] = "This email already has an account."
    if errors:
        return api_error(400, "Please correct the highlighted fields.", errors)

    with transaction.atomic():      # all three rows are saved, or none
        new_household = Household.objects.create(**household)
        new_member = HouseholdMember.objects.create(household=new_household, **member)
        AccountHolder.objects.create(member=new_member, login_email=creds["login_email"],
                                     password_hash=make_password(creds["password"]))
    set_current_user(request, {"role": "household", "member_id": new_member.member_id})
    return JsonResponse(get_current_user(request), status=201)


# ------------------------------------------------------------------ household
@household_required
@require_http_methods(["GET", "PATCH"])
def household(request):
    household_id = request.current_user["household_id"]
    if request.method == "GET":
        return _household_response(household_id)

    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    clean, errors = serializers.validate_household(data, partial=True)
    if "zone_id" in clean and not EvacuationZone.objects.filter(pk=clean["zone_id"]).exists():
        errors["zone_id"] = "Choose an evacuation zone from the list."
    if errors:
        return api_error(400, "Please correct the highlighted fields.", errors)
    if clean:
        Household.objects.filter(pk=household_id).update(**clean)
    return _household_response(household_id)


@household_required
@require_http_methods(["POST"])
def members(request):
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    clean, errors = serializers.validate_member(data)
    if errors:
        return api_error(400, "Please correct the highlighted fields.", errors)
    HouseholdMember.objects.create(household_id=request.current_user["household_id"], **clean)
    return _household_response(request.current_user["household_id"], status=201)


def _own_member(request, member_id):
    """The member, only if it belongs to the logged-in user's household."""
    return HouseholdMember.objects.filter(
        pk=member_id, household_id=request.current_user["household_id"]).first()


@household_required
@require_http_methods(["PATCH", "DELETE"])
def member_detail(request, member_id):
    member = _own_member(request, member_id)
    if member is None:
        return api_error(404, "This member was not found in your household.")
    household_id = request.current_user["household_id"]

    if request.method == "PATCH":
        data = read_json(request)
        if data is None:
            return api_error(400, "Send JSON data.")
        clean, errors = serializers.validate_member(data, partial=True)
        if errors:
            return api_error(400, "Please correct the highlighted fields.", errors)
        if clean:
            HouseholdMember.objects.filter(pk=member.member_id).update(**clean)
        return _household_response(household_id)

    # DELETE
    if member.member_id == request.current_user["member_id"]:
        return api_error(409, "You cannot remove yourself while you are logged in.")
    with transaction.atomic():
        is_holder = AccountHolder.objects.filter(pk=member.member_id).exists()
        holders = AccountHolder.objects.select_for_update().filter(
            member__household_id=household_id).count()
        if is_holder and holders <= 1:
            return api_error(409, "A household must keep at least one account holder.")
        if _member_is_referenced(member.member_id):
            return api_error(409, "This member is part of a registration, so they cannot be removed.")
        AccountHolder.objects.filter(pk=member.member_id).delete()
        HouseholdMember.objects.filter(pk=member.member_id).delete()
    return _household_response(household_id)


@household_required
@require_http_methods(["POST"])
def member_account(request, member_id):
    """Give another member of the same household their own login."""
    member = _own_member(request, member_id)
    if member is None:
        return api_error(404, "This member was not found in your household.")
    data = read_json(request)
    if data is None:
        return api_error(400, "Send JSON data.")
    creds, errors = serializers.validate_credentials(data)
    if AccountHolder.objects.filter(pk=member.member_id).exists():
        return api_error(409, "This member already has a login.")
    if "login_email" in creds and _email_in_use(creds["login_email"]):
        errors["login_email"] = "This email already has an account."
    if errors:
        return api_error(400, "Please correct the highlighted fields.", errors)
    AccountHolder.objects.create(member=member, login_email=creds["login_email"],
                                 password_hash=make_password(creds["password"]))
    return _household_response(request.current_user["household_id"], status=201)
