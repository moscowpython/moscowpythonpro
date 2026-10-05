from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

MOSCOW = ZoneInfo("Europe/Moscow")


def upcoming_condition(now):
    midnight = datetime.combine(now.astimezone(MOSCOW).date(), time.min, tzinfo=MOSCOW)
    return Q(ends_at__gt=now) | Q(ends_at__isnull=True, starts_at__gte=midnight)


class EventQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def upcoming(self, now):
        return self.filter(upcoming_condition(now)).order_by("starts_at", "pk")

    def archive(self, now):
        return self.exclude(upcoming_condition(now)).order_by("-starts_at", "-pk")


class Event(models.Model):
    title = models.CharField("Название", max_length=300)
    starts_at = models.DateTimeField("Начало")
    ends_at = models.DateTimeField("Окончание", blank=True, null=True)
    format = models.CharField("Формат", max_length=150)
    speakers = models.TextField("Спикеры", blank=True, help_text="Один спикер на строку")
    short_description = models.TextField("Краткое описание", blank=True)
    registration_url = models.URLField(
        "Ссылка на регистрацию",
        max_length=1000,
        blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )
    location = models.CharField("Место", max_length=300, blank=True)
    is_published = models.BooleanField("Опубликовано", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        verbose_name = "мероприятие"
        verbose_name_plural = "мероприятия"
        ordering = ["starts_at", "pk"]
        indexes = [models.Index(fields=["is_published", "starts_at"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__isnull=True) | Q(ends_at__gt=models.F("starts_at")),
                name="event_end_after_start",
            )
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Окончание должно быть позже начала."})

    @property
    def speaker_names(self):
        return [line.strip() for line in self.speakers.splitlines() if line.strip()]

    def status_at(self, now):
        today = now.astimezone(MOSCOW).date()
        day = self.starts_at.astimezone(MOSCOW).date()
        if (self.ends_at and self.ends_at <= now) or (not self.ends_at and day < today):
            return "Прошедшее"
        return "Сегодня" if day <= today else "Будущее"

    @property
    def status(self):
        return self.status_at(timezone.now())
