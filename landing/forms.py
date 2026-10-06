from io import BytesIO
from uuid import uuid4

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps

from .models import Resident


class ResidentAdminForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = "__all__"

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo or "photo" not in self.changed_data:
            return photo
        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Фото должно быть не больше 5 МБ.")
        photo.seek(0)
        try:
            with Image.open(photo) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise forms.ValidationError("Используйте JPEG, PNG или WebP.")
                if source.width * source.height > 20_000_000:
                    raise forms.ValidationError("Фото должно быть не больше 20 мегапикселей.")
                portrait = ImageOps.exif_transpose(source).convert("RGBA")
                portrait.thumbnail((640, 800), Image.Resampling.LANCZOS)
                background = Image.new("RGB", portrait.size, "white")
                background.paste(portrait, mask=portrait.getchannel("A"))
                output = BytesIO()
                background.save(output, format="WEBP", quality=88)
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            raise forms.ValidationError("Не удалось прочитать фото.") from exc
        return SimpleUploadedFile(f"{uuid4().hex}.webp", output.getvalue(), "image/webp")
