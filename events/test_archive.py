from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase

from .models import Event
from .tests import NOW


class ArchivePageTests(TestCase):
    def setUp(self):
        Event.objects.all().delete()

    def page(self, query=""):
        with patch("landing.views.timezone.now", return_value=NOW):
            return self.client.get("/archive/" + query)

    def test_empty_archive_and_home_link(self):
        response = self.page()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Прошедших мероприятий пока нет")
        self.assertContains(response, 'href="/#schedule"')
        self.assertContains(self.client.get("/"), 'href="/archive/"')

    def test_pagination_publication_sorting_and_registration(self):
        for i in range(1, 23):
            Event.objects.create(
                title=f"Встреча {i}",
                format="Круглый стол",
                starts_at=NOW - timedelta(days=i),
                registration_url="https://moscowdjango.timepad.ru/event/4201922/",
            )
        Event.objects.create(
            title="Будущая встреча", format="Воркшоп", starts_at=NOW + timedelta(days=1)
        )
        Event.objects.create(
            title="Скрытая встреча",
            format="Воркшоп",
            starts_at=NOW - timedelta(days=1),
            is_published=False,
        )
        Event.objects.create(title="Ещё идёт", format="Воркшоп", starts_at=NOW - timedelta(hours=1))
        response = self.page()
        self.assertEqual(
            [e.title for e in response.context["page"]], [f"Встреча {i}" for i in range(1, 21)]
        )
        for text in [
            "Будущая встреча",
            "Скрытая встреча",
            "Ещё идёт",
            "Зарегистрироваться",
            "Регистрация скоро",
        ]:
            self.assertNotContains(response, text)
        second = self.page("?page=2")
        self.assertEqual([e.title for e in second.context["page"]], ["Встреча 21", "Встреча 22"])
        self.assertTrue(second.context["canonical_url"].endswith("/archive/?page=2"))
        self.assertEqual(self.page("?page=invalid").status_code, 200)
