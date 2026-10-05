import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


class DefaultAdminTests(TestCase):
    def configure(self, login="", password=""):
        output = StringIO()
        with patch.dict(
            os.environ, {"DEFAULT_ADMIN_LOGIN": login, "DEFAULT_ADMIN_PASSWORD": password}
        ):
            call_command("setup_default_admin", stdout=output)
        return output.getvalue()

    def test_missing_credentials_leave_users_unchanged(self):
        user = get_user_model().objects.create_user("tester", password="original")
        original_hash = user.password
        for login, password in [("", ""), ("tester", ""), ("", "test-password")]:
            with self.subTest(login=login, password_present=bool(password)):
                self.configure(login, password)
                user.refresh_from_db()
                self.assertEqual(user.password, original_hash)
                self.assertFalse(user.is_superuser)
                self.assertEqual(get_user_model().objects.count(), 1)

    def test_create_admin_and_repeat_without_duplicates(self):
        output = self.configure("tester", "test-password")
        user = get_user_model().objects.get(username="tester")
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser)
        self.assertTrue(user.check_password("test-password"))
        self.assertNotEqual(user.password, "test-password")
        self.assertNotIn("test-password", output)
        original_hash = user.password
        self.configure("tester", "test-password")
        user.refresh_from_db()
        self.assertEqual(user.password, original_hash)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertTrue(self.client.login(username="tester", password="test-password"))
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_existing_user_password_and_admin_flags_updated(self):
        user = get_user_model().objects.create_user("tester", password="old", is_active=False)
        self.configure("tester", "new-test-password")
        user.refresh_from_db()
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser)
        self.assertTrue(user.check_password("new-test-password"))
        self.assertFalse(user.check_password("old"))
        self.assertEqual(get_user_model().objects.count(), 1)
