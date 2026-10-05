from datetime import timedelta

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from events.models import Event


@override_settings(
    ALLOWED_HOSTS=["*"],
    SITE_URL_FROM_REQUEST=True,
    SITE_URL="",
    SECURE_SSL_REDIRECT=False,
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    CSRF_TRUSTED_ORIGINS=[],
)
class SiteOriginTests(TestCase):
    def test_assigned_hostname_used_in_all_public_urls(self):
        event = Event.objects.create(
            title="Встреча", format="Круглый стол", starts_at=timezone.now() + timedelta(days=1)
        )
        response = self.client.get(
            "/", HTTP_HOST="assigned-test-host.test", HTTP_X_FORWARDED_PROTO="https"
        )
        self.assertContains(
            response, '<link rel="canonical" href="https://assigned-test-host.test/">'
        )
        self.assertContains(response, 'content="https://assigned-test-host.test/static/images/og.')
        self.assertContains(response, f'"url": "https://assigned-test-host.test/#event-{event.pk}"')

    @override_settings(SITE_URL_FROM_REQUEST=False, SITE_URL="https://fixed-host.test")
    def test_fixed_origin_remains_default(self):
        response = self.client.get("/", HTTP_HOST="another-host.test")
        self.assertContains(response, '<link rel="canonical" href="https://fixed-host.test/">')

    def test_admin_csrf_accepts_same_origin_and_rejects_foreign_origin(self):
        client = Client(enforce_csrf_checks=True)
        headers = {"HTTP_HOST": "assigned-test-host.test", "HTTP_X_FORWARDED_PROTO": "https"}
        client.get("/admin/login/", **headers)
        data = {
            "username": "nonexistent",
            "password": "invalid",
            "csrfmiddlewaretoken": client.cookies[settings.CSRF_COOKIE_NAME].value,
        }
        same_origin = client.post(
            "/admin/login/", data, HTTP_ORIGIN="https://assigned-test-host.test", **headers
        )
        self.assertEqual(same_origin.status_code, 200)
        foreign_origin = client.post(
            "/admin/login/", data, HTTP_ORIGIN="https://unrelated-host.test", **headers
        )
        self.assertEqual(foreign_origin.status_code, 403)
