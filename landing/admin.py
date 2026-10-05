from django.contrib import admin

from .models import Resident


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "position", "order", "is_published"]
    list_editable = ["order", "is_published"]
    list_filter = ["is_published"]
    search_fields = ["name", "company"]
    readonly_fields = ["created_at", "updated_at"]
