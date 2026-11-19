"""Validation of incoming data and conversion of rows to JSON (plain functions, no extra library)."""
import datetime
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8      # assumption: the requirements give no password rule

HOUSEHOLD_FIELDS = {"street": 255, "city": 100, "province": 100, "postal_code": 20}   # same as schema-v1.sql
MEMBER_NAME_FIELDS = {"first_name": 100, "last_name": 100}


def _text(data, field, max_length, errors, required=True):
    value = data.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            errors[field] = "This field is required."
        return None
    if not isinstance(value, str):
        errors[field] = "This field must be text."
        return None
    value = value.strip()
    if len(value) > max_length:
        errors[field] = f"Use at most {max_length} characters."
        return None
    return value


def validate_household(data, partial=False):
    """Returns (clean values, errors). With partial=True only the given fields are checked."""
    clean, errors = {}, {}
    for field, max_length in HOUSEHOLD_FIELDS.items():
        if partial and field not in data:
            continue
        value = _text(data, field, max_length, errors)
        if value is not None:
            clean[field] = value
    if not partial or "zone_id" in data:
        zone_id = data.get("zone_id")
        if isinstance(zone_id, bool) or not isinstance(zone_id, int):
            errors["zone_id"] = "Choose an evacuation zone."
        else:
            clean["zone_id"] = zone_id
    return clean, errors


def validate_member(data, partial=False):
    clean, errors = {}, {}
    for field, max_length in MEMBER_NAME_FIELDS.items():
        if partial and field not in data:
            continue
        value = _text(data, field, max_length, errors)
        if value is not None:
            clean[field] = value
    if not partial or "date_of_birth" in data:
        raw = data.get("date_of_birth")
        try:
            dob = datetime.date.fromisoformat(raw) if isinstance(raw, str) else None
        except ValueError:
            dob = None
        if dob is None:
            errors["date_of_birth"] = "Enter a valid date (YYYY-MM-DD)."
        elif dob > datetime.date.today():
            errors["date_of_birth"] = "The date of birth cannot be in the future."
        else:
            clean["date_of_birth"] = dob
    if "phone_number" in data:          # optional field
        phone = data.get("phone_number")
        if phone is None or (isinstance(phone, str) and not phone.strip()):
            clean["phone_number"] = None
        else:
            value = _text(data, "phone_number", 30, errors)
            if value is not None:
                clean["phone_number"] = value
    elif not partial:
        clean["phone_number"] = None
    return clean, errors


def validate_credentials(data):
    clean, errors = {}, {}
    email = _text(data, "login_email", 254, errors)
    if email is not None:
        email = email.lower()
        if not EMAIL_RE.match(email):
            errors["login_email"] = "Enter a valid email address."
        else:
            clean["login_email"] = email
    password = data.get("password")
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Use at least {MIN_PASSWORD_LENGTH} characters."
    else:
        clean["password"] = password
    return clean, errors


def member_to_dict(member, account_emails):
    """account_emails maps member_id -> login email for members who have a login."""
    return {
        "member_id": member.member_id,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "date_of_birth": member.date_of_birth.isoformat(),
        "phone_number": member.phone_number,
        "is_account_holder": member.member_id in account_emails,
        "login_email": account_emails.get(member.member_id),
    }


def household_to_dict(household, members, account_emails):
    return {
        "household_id": household.household_id,
        "street": household.street,
        "city": household.city,
        "province": household.province,
        "postal_code": household.postal_code,
        "zone": {"zone_id": household.zone.zone_id, "zone_name": household.zone.zone_name},
        "members": [member_to_dict(m, account_emails) for m in members],
    }
