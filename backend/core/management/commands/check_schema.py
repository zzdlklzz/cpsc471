from django.core.management.base import BaseCommand

from core import models


class Command(BaseCommand):
    help = "Count the rows of every model Person 1 uses, so we know the models match the tables."

    def handle(self, *args, **options):
        checks = [
            models.EvacuationZone, models.Household, models.HouseholdMember, models.AccountHolder,
            models.Staff, models.EmergencyEvent, models.EvacuationNotice, models.NoticeZone,
        ]
        for model in checks:
            count = model.objects.count()
            self.stdout.write(f"{model._meta.db_table:20s} {count} rows")
        # Follow the foreign keys once, which proves the column names are right.
        first = models.Household.objects.select_related("zone").first()
        if first:
            self.stdout.write(f"Household {first.household_id} is in zone: {first.zone.zone_name}")
        nz = models.NoticeZone.objects.select_related("notice", "zone").first()
        if nz:
            self.stdout.write(f"Notice '{nz.notice.title}' targets zone: {nz.zone.zone_name}")
        self.stdout.write(self.style.SUCCESS("Models match the schema."))
