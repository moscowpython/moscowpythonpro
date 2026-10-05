from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import MOSCOW, Event

NOW = datetime(2026, 10, 5, 18, tzinfo=MOSCOW)


class EventTests(TestCase):
    def setUp(self):
        Event.objects.all().delete()

    def event(self, title="Встреча", **kwargs):
        return Event.objects.create(
            title=title,
            starts_at=kwargs.pop("starts_at", NOW + timedelta(days=1)),
            format="Круглый стол, 2 ч.",
            **kwargs,
        )

    def page(self, now=NOW):
        with patch("landing.views.timezone.now", return_value=now):
            return self.client.get("/")

    def test_public_health_admin(self):
        self.assertEqual(self.page().status_code, 200)
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertRedirects(self.client.get("/admin/"), "/admin/login/?next=/admin/")

    def test_hidden_events_absent_everywhere(self):
        self.event("Скрытая встреча", is_published=False)
        self.event("Скрытый архив", is_published=False, starts_at=NOW - timedelta(days=2))
        response = self.page()
        self.assertNotContains(response, "Скрытая")
        self.assertNotContains(response, "Скрытый")
        self.assertIsNone(response.context["next_event"])

    def test_sorting_archive_and_next(self):
        late = self.event("Позже", starts_at=NOW + timedelta(days=3))
        soon = self.event("Скоро")
        past = self.event("Прошло", starts_at=NOW - timedelta(days=1))
        today = self.event("Сегодня", starts_at=NOW - timedelta(hours=2))
        response = self.page()
        self.assertEqual(response.context["upcoming"], [today, soon, late])
        self.assertEqual(list(response.context["archive"]), [past])
        self.assertEqual(response.context["next_event"], soon)

    def test_end_boundary_and_multiday(self):
        event = self.event(starts_at=NOW - timedelta(days=1), ends_at=NOW)
        self.assertIn(event, Event.objects.upcoming(NOW - timedelta(microseconds=1)))
        self.assertNotIn(event, Event.objects.upcoming(NOW))
        self.assertIn(event, Event.objects.archive(NOW))
        self.assertIn(event, Event.objects.archive(NOW + timedelta(seconds=1)))
        self.assertEqual(event.status_at(NOW), "Прошедшее")

    def test_no_end_uses_moscow_midnight_not_utc(self):
        event = self.event(starts_at=datetime(2026, 10, 5, 0, 30, tzinfo=MOSCOW))
        before = datetime(2026, 10, 5, 20, 59, 59, tzinfo=UTC)
        after = datetime(2026, 10, 5, 21, 0, tzinfo=UTC)
        self.assertIn(event, Event.objects.upcoming(before))
        self.assertNotIn(event, Event.objects.upcoming(after))
        self.assertIn(event, Event.objects.archive(after))

    def test_archive_limit_order_and_no_registration(self):
        for i in range(1, 8):
            self.event(
                f"Архив {i}",
                starts_at=NOW - timedelta(days=i),
                registration_url=f"https://moscowdjango.timepad.ru/event/{i}/",
            )
        response = self.page()
        self.assertEqual(
            [e.title for e in response.context["archive"]], [f"Архив {i}" for i in range(1, 6)]
        )
        self.assertNotContains(response, "moscowdjango.timepad.ru/event/")
        self.assertNotContains(response, 'class="next-event"')

    def test_registration_link_or_pending(self):
        event = self.event()
        response = self.page()
        self.assertContains(response, "Регистрация скоро")
        self.assertNotContains(response, "Зарегистрироваться")
        event.registration_url = "https://moscowdjango.timepad.ru/event/4201922/"
        event.save()
        self.assertContains(
            self.page(),
            f'href="{event.registration_url}" target="_blank" rel="noopener noreferrer"',
        )

    def test_empty_sections(self):
        response = self.page()
        self.assertContains(response, "Новые мероприятия скоро")
        self.assertNotContains(response, 'class="archive"')
        self.assertNotContains(response, 'class="next-event"')

    def test_invalid_end(self):
        event = Event(title="Встреча", format="Воркшоп", starts_at=NOW, ends_at=NOW)
        with self.assertRaises(ValidationError):
            event.full_clean()
        event.ends_at = None
        event.registration_url = "ftp://moscowpython.ru/file"
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_speaker_lines(self):
        event = self.event(speakers=" Александр Ковалёв \r\n\nСурен Хоренян ")
        self.assertEqual(event.speaker_names, ["Александр Ковалёв", "Сурен Хоренян"])

    def test_admin_save_immediately_changes_page(self):
        user = get_user_model().objects.create_superuser("organizer", password="test-password-only")
        self.client.force_login(user)
        event = self.event()
        response = self.client.post(
            reverse("admin:events_event_change", args=[event.pk]),
            {
                "title": "Обновлённая тема",
                "starts_at_0": "2026-10-06",
                "starts_at_1": "19:00:00",
                "ends_at_0": "",
                "ends_at_1": "",
                "format": "Кейс-клуб",
                "speakers": "Сурен Хоренян",
                "short_description": "Новый разбор",
                "registration_url": "",
                "location": "Москва",
                "is_published": "on",
                "_save": "Сохранить",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.page(), "Обновлённая тема")
        event.refresh_from_db()
        self.assertEqual(event.starts_at.astimezone(MOSCOW).hour, 19)

    def test_schema_escapes_user_content(self):
        self.event('</script><script>alert("x")</script>')
        response = self.page()
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertContains(response, r"\u003C/script\u003E")
