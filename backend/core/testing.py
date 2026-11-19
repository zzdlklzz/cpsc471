"""Small helpers that create test rows. Used by the tests of every app."""
import datetime

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.utils import timezone

from .models import (AccountHolder, EmergencyEvent, EvacuationNotice, EvacuationZone,
                     Household, HouseholdMember, Staff)

PASSWORD = "Test-pass-123"


def make_zone(name="Zone A"):
    return EvacuationZone.objects.create(zone_name=name)


def make_member(household, first="Sam", last="Lee", dob=datetime.date(1990, 1, 1)):
    return HouseholdMember.objects.create(first_name=first, last_name=last, date_of_birth=dob,
                                          phone_number=None, household=household)


def make_account(member, email):
    return AccountHolder.objects.create(member=member, login_email=email,
                                        password_hash=make_password(PASSWORD))


def make_household(zone, email="holder@example.com", first="Anh", last="Nguyen"):
    """Returns (household, first member, account holder)."""
    household = Household.objects.create(street="1 Test St", city="Calgary", province="Alberta",
                                         postal_code="T2N 1N4", zone=zone)
    member = make_member(household, first, last)
    return household, member, make_account(member, email)


def make_staff(email="staff@example.com"):
    return Staff.objects.create(name="Staff Person", login_email=email,
                                password_hash=make_password(PASSWORD))


def make_event(name="Test Wildfire", status="Active"):
    return EmergencyEvent.objects.create(name=name, event_type="Wildfire",
                                         start_date=datetime.date(2026, 8, 1), end_date=None, status=status)


def make_notice(event, staff, zones, title="Notice", when=None):
    when = when or datetime.datetime(2026, 8, 2, 12, 0, 0)
    if settings.USE_TZ and timezone.is_naive(when):
        when = timezone.make_aware(when, datetime.timezone.utc)
    notice = EvacuationNotice.objects.create(
        title=title, message="Message text", event=event, staff=staff, published_at=when)
    with connection.cursor() as cur:
        for zone in zones:
            cur.execute("INSERT INTO NOTICE_ZONE (notice_id, zone_id) VALUES (%s, %s)",
                        [notice.notice_id, zone.zone_id])
    return notice
