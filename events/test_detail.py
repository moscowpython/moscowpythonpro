import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase

from .models import Event
from .tests import NOW


class EventDetailTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Инженерные решения",
            format="Круглый стол",
            starts_at=NOW + timedelta(days=1),
            speakers="Александр Ковалёв\nСурен Хоренян",
            short_description="Обсуждаем решения",
            location="Москва",
            registration_url="https://moscowdjango.timepad.ru/event/4201922/",
        )

    def page(self):
        with patch("landing.views.timezone.now", return_value=NOW):
            return self.client.get(self.event.get_absolute_url())

    def test_details_metadata_and_links(self):
        response = self.page()
        self.assertEqual(response.status_code, 200)
        for text in [
            self.event.title,
            "Сурен Хоренян",
            self.event.short_description,
            self.event.location,
            "Зарегистрироваться",
            'rel="noopener noreferrer"',
        ]:
            self.assertContains(response, text)
        schema = json.loads(response.context["schema_json"])
        self.assertEqual(schema["url"], response.context["canonical_url"])
        self.assertTrue(schema["url"].endswith(self.event.get_absolute_url()))
        with patch("landing.views.timezone.now", return_value=NOW):
            self.assertContains(self.client.get("/"), f'href="{self.event.get_absolute_url()}"')
        url = self.event.get_absolute_url()
        self.event.title = "Другое название"
        self.event.save()
        self.assertEqual(self.event.get_absolute_url(), url)

    def test_hidden_and_missing(self):
        self.event.is_published = False
        self.event.save()
        self.assertEqual(self.page().status_code, 404)
        self.assertEqual(self.client.get("/events/999999/").status_code, 404)

    def test_missing_registration(self):
        self.event.registration_url = ""
        self.event.save()
        self.assertContains(self.page(), "Регистрация скоро")
        self.assertNotContains(self.page(), "Зарегистрироваться")

    def test_past_and_end_time_boundary(self):
        self.event.starts_at = NOW - timedelta(hours=1)
        self.event.ends_at = NOW
        self.event.save()
        response = self.page()
        self.assertContains(response, "Мероприятие завершилось")
        self.assertNotContains(response, "Зарегистрироваться")
        with patch("landing.views.timezone.now", return_value=NOW):
            for path in ["/", "/archive/"]:
                self.assertContains(
                    self.client.get(path), f'href="{self.event.get_absolute_url()}"'
                )

    def test_user_content_is_escaped(self):
        self.event.short_description = "</script><script>alert(1)</script>"
        self.event.save()
        response = self.page()
        self.assertNotContains(response, self.event.short_description)
        self.assertEqual(
            json.loads(response.context["schema_json"])["description"], self.event.short_description
        )
