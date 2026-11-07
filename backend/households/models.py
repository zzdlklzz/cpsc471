"""Mappings to existing SQL-owned tables; these models do not manage schema."""

from django.db import models


class EvacuationZone(models.Model):
    zone_id = models.AutoField(primary_key=True)
    zone_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "EVACUATION_ZONE"


class Household(models.Model):
    household_id = models.AutoField(primary_key=True)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    zone = models.ForeignKey(
        EvacuationZone,
        models.PROTECT,
        db_column="zone_id",
        related_name="households",
    )

    class Meta:
        managed = False
        db_table = "HOUSEHOLD"


class HouseholdMember(models.Model):
    member_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    household = models.ForeignKey(
        Household,
        models.PROTECT,
        db_column="household_id",
        related_name="members",
    )

    class Meta:
        managed = False
        db_table = "HOUSEHOLD_MEMBER"


class AccountHolder(models.Model):
    member = models.OneToOneField(
        HouseholdMember, models.PROTECT, primary_key=True,
        db_column="member_id", related_name="account_holder",
    )
    login_email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "ACCOUNT_HOLDER"
