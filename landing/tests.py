from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Resident


class ResidentTests(TestCase):
    def setUp(self):
        Resident.objects.all().delete()

    def test_publication_and_order(self):
        second = Resident.objects.create(
            name="Сурен Хоренян", company="Яндекс", position="Разработчик", order=2
        )
        first = Resident.objects.create(
            name="Александр Ковалёв", company="Ozon Tech", position="Руководитель", order=1
        )
        Resident.objects.create(name="Скрытый резидент", is_published=False)
        response = self.client.get("/")
        self.assertEqual(list(response.context["residents"]), [first, second])
        self.assertNotContains(response, "Скрытый резидент")

    def test_admin_crud_reflected_on_page(self):
        user = get_user_model().objects.create_superuser("organizer", password="test-password-only")
        self.client.force_login(user)
        data = {
            "name": "Александр Ковалёв",
            "company": "Ozon Tech",
            "position": "Руководитель",
            "bio": "Короткая биография",
            "website": "",
            "order": "1",
            "is_published": "on",
        }
        self.assertEqual(
            self.client.post(reverse("admin:landing_resident_add"), data).status_code, 302
        )
        resident = Resident.objects.get()
        self.assertContains(self.client.get("/"), "Короткая биография")
        data["bio"] = "Обновлённая биография"
        self.assertEqual(
            self.client.post(
                reverse("admin:landing_resident_change", args=[resident.pk]), data
            ).status_code,
            302,
        )
        self.assertContains(self.client.get("/"), "Обновлённая биография")
        del data["is_published"]
        self.client.post(reverse("admin:landing_resident_change", args=[resident.pk]), data)
        self.assertNotContains(self.client.get("/"), "Обновлённая биография")
        self.assertEqual(
            self.client.post(
                reverse("admin:landing_resident_delete", args=[resident.pk]), {"post": "yes"}
            ).status_code,
            302,
        )
        self.assertFalse(Resident.objects.exists())
