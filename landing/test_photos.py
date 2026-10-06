from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .forms import ResidentAdminForm
from .models import Resident


def upload(format="PNG"):
    buffer = BytesIO()
    Image.new("RGB", (900, 1200), "white").save(buffer, format=format)
    return SimpleUploadedFile(
        f"portrait.{format.lower()}", buffer.getvalue(), f"image/{format.lower()}"
    )


class ResidentPhotoTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(MEDIA_ROOT=directory.name)
        override.enable()
        self.addCleanup(override.disable)
        self.user = get_user_model().objects.create_superuser("photo-editor", password="test-only")
        self.client.force_login(self.user)
        self.resident = Resident.objects.create(
            name="Александр Ковалёв", company="Ozon Tech", position="Руководитель"
        )
        self.data = {
            "name": self.resident.name,
            "company": self.resident.company,
            "position": self.resident.position,
            "order": "1",
            "is_published": "on",
        }
        self.url = reverse("admin:landing_resident_change", args=[self.resident.pk])

    def test_admin_upload_converts_and_public_photo_is_served(self):
        response = self.client.post(self.url, {**self.data, "photo": upload()})
        self.assertEqual(response.status_code, 302)
        self.resident.refresh_from_db()
        self.assertTrue(self.resident.photo.name.endswith(".webp"))
        with self.resident.photo.open("rb") as file, Image.open(file) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertLessEqual(image.width, 640)
            self.assertLessEqual(image.height, 800)
        self.client.logout()
        self.assertContains(self.client.get("/"), self.resident.photo.url)
        response = self.client.get(self.resident.photo.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/webp")
        response.close()
        self.resident.is_published = False
        self.resident.save()
        self.assertEqual(self.client.get(self.resident.photo.url).status_code, 404)
        self.client.force_login(self.user)
        response = self.client.get(self.resident.photo.url)
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_admin_photo_can_be_removed(self):
        self.client.post(self.url, {**self.data, "photo": upload()})
        self.resident.refresh_from_db()
        previous_url = self.resident.photo.url
        response = self.client.post(self.url, {**self.data, "photo-clear": "on"})
        self.assertEqual(response.status_code, 302)
        self.resident.refresh_from_db()
        self.assertFalse(self.resident.photo)
        self.assertNotContains(self.client.get("/"), previous_url)
        self.assertEqual(self.client.get(previous_url).status_code, 404)

    def test_unsupported_and_invalid_uploads_rejected(self):
        for file in [upload("GIF"), SimpleUploadedFile("portrait.png", b"not an image")]:
            form = ResidentAdminForm(data=self.data, files={"photo": file}, instance=self.resident)
            self.assertFalse(form.is_valid())
            self.assertIn("photo", form.errors)

    def test_photo_optional_and_missing_file_returns_404(self):
        self.assertContains(self.client.get("/"), self.resident.name)
        self.assertEqual(self.client.get("/media/residents/missing.webp").status_code, 404)
        self.resident.photo = "residents/missing.webp"
        self.resident.save()
        self.assertEqual(self.client.get(self.resident.photo.url).status_code, 404)
