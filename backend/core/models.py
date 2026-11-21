"""Shared models for the tables that Person 1 reads or writes.

Every model has managed = False, because the tables are created by backend/sql/schema-v2.sql
(the team's agreed schema). Django only reads and writes rows. It never runs
migrations for these tables.

Persons 2 and 3 add their own models (REGISTRATION, PLACEMENT, SHELTER, ...) in this
file or in their own app, using the same pattern.
"""
from django.db import models


class EvacuationZone(models.Model):
    zone_id = models.AutoField(primary_key=True)
    zone_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "EVACUATION_ZONE"

    def __str__(self):
        return self.zone_name


class Household(models.Model):
    household_id = models.AutoField(primary_key=True)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    zone = models.ForeignKey(EvacuationZone, db_column="zone_id", on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "HOUSEHOLD"


class HouseholdMember(models.Model):
    member_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=30, null=True, blank=True)
    household = models.ForeignKey(
        Household, db_column="household_id", on_delete=models.DO_NOTHING, related_name="members"
    )

    class Meta:
        managed = False
        db_table = "HOUSEHOLD_MEMBER"


class AccountHolder(models.Model):
    """A household member who has a login. The primary key is also the member id."""
    member = models.OneToOneField(
        HouseholdMember, db_column="member_id", primary_key=True,
        on_delete=models.DO_NOTHING, related_name="account",
    )
    login_email = models.CharField(max_length=254, unique=True)
    password_hash = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "ACCOUNT_HOLDER"


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    login_email = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "STAFF"


class EmergencyEvent(models.Model):
    event_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    event_type = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = "EMERGENCY_EVENT"


class EvacuationNotice(models.Model):
    notice_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    message = models.TextField()
    published_at = models.DateTimeField()
    event = models.ForeignKey(EmergencyEvent, db_column="event_id", on_delete=models.DO_NOTHING)
    staff = models.ForeignKey(Staff, db_column="staff_id", on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "EVACUATION_NOTICE"


class NoticeZone(models.Model):
    """Junction table. The primary key is (notice_id, zone_id)."""
    pk = models.CompositePrimaryKey("notice_id", "zone_id")
    notice = models.ForeignKey(
        EvacuationNotice, db_column="notice_id", on_delete=models.DO_NOTHING, related_name="notice_zones"
    )
    zone = models.ForeignKey(
        EvacuationZone, db_column="zone_id", on_delete=models.DO_NOTHING, related_name="notice_zones"
    )

    class Meta:
        managed = False
        db_table = "NOTICE_ZONE"
