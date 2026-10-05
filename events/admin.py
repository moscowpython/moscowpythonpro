from django.contrib import admin
from django.utils.html import format_html

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "starts_at",
        "title",
        "format",
        "speakers",
        "registration",
        "is_published",
        "event_status",
    ]
    list_filter = ["is_published", "format"]
    search_fields = ["title", "speakers"]
    date_hierarchy = "starts_at"
    ordering = ["starts_at"]
    readonly_fields = ["event_status", "created_at", "updated_at"]
    fields = [
        "title",
        ("starts_at", "ends_at"),
        "format",
        "speakers",
        "short_description",
        "registration_url",
        "location",
        "is_published",
        "event_status",
        "created_at",
        "updated_at",
    ]

    @admin.display(description="Регистрация")
    def registration(self, obj):
        if obj.registration_url:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">Открыть ↗</a>',
                obj.registration_url,
            )
        return "Скоро"

    @admin.display(description="Статус")
    def event_status(self, obj):
        return obj.status if obj and obj.starts_at else "—"
