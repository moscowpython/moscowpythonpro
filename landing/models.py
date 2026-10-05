from django.core.validators import URLValidator
from django.db import models


class Resident(models.Model):
    name = models.CharField("Имя", max_length=200)
    company = models.CharField("Компания", max_length=200)
    position = models.CharField("Должность", max_length=300)
    bio = models.TextField("Короткая биография", blank=True, help_text="1–3 предложения")
    website = models.URLField(
        "Ссылка", blank=True, max_length=1000, validators=[URLValidator(schemes=["http", "https"])]
    )
    order = models.PositiveIntegerField("Порядок", default=0)
    is_published = models.BooleanField("Опубликован", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ["order", "name", "pk"]
        verbose_name = "резидент"
        verbose_name_plural = "резиденты"

    def __str__(self):
        return self.name
