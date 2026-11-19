import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from core.models import AccountHolder, Staff


class Command(BaseCommand):
    help = "Replace the fake password hashes in the seed data with real hashes of DEMO_PASSWORD (from .env)."

    def handle(self, *args, **options):
        password = os.environ.get("DEMO_PASSWORD")
        if not password:
            self.stderr.write("Set DEMO_PASSWORD in backend/.env first.")
            return
        n = 0
        for account in AccountHolder.objects.all():
            account.password_hash = make_password(password)
            account.save(update_fields=["password_hash"])
            n += 1
        for member in Staff.objects.all():
            member.password_hash = make_password(password)
            member.save(update_fields=["password_hash"])
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {n} demo accounts. Log in with the password in DEMO_PASSWORD."))
