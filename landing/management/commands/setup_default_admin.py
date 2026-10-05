import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Create or update the test administrator when both DEFAULT_ADMIN variables are set."

    def handle(self, *args, **options):
        login = os.getenv("DEFAULT_ADMIN_LOGIN", "")
        password = os.getenv("DEFAULT_ADMIN_PASSWORD", "")
        if not login or not password:
            self.stdout.write("Default administrator skipped: both variables are required.")
            return

        User = get_user_model()
        with transaction.atomic():
            user, _ = User.objects.get_or_create(**{User.USERNAME_FIELD: login})
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            if not user.check_password(password):
                user.set_password(password)
            user.save()
        self.stdout.write(self.style.SUCCESS("Default administrator configured."))
