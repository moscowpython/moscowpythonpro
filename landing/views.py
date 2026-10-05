import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_safe

from events.models import MOSCOW, Event

from .models import Resident


def event_schema(event, site_url):
    item = {
        "@type": "Event",
        "name": event.title,
        "startDate": event.starts_at.astimezone(MOSCOW).isoformat(),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "url": f"{site_url}/#event-{event.pk}",
        "organizer": {
            "@type": "Organization",
            "name": "Moscow Python",
            "url": "https://moscowpython.ru/",
        },
    }
    if event.ends_at:
        item["endDate"] = event.ends_at.astimezone(MOSCOW).isoformat()
    if event.short_description:
        item["description"] = event.short_description
    if event.location:
        item["location"] = {"@type": "Place", "name": event.location}
    if event.speaker_names:
        item["performer"] = [{"@type": "Person", "name": n} for n in event.speaker_names]
    return item


@require_safe
def index(request):
    site_url = (
        request.build_absolute_uri("/").rstrip("/")
        if settings.SITE_URL_FROM_REQUEST
        else settings.SITE_URL
    )
    now = timezone.now()
    published = Event.objects.published()
    upcoming = list(published.upcoming(now))
    future = [event for event in upcoming if event.starts_at > now]
    schema = {"@context": "https://schema.org", "@graph": [event_schema(e, site_url) for e in future]}
    # JSON inside a script element must not allow a literal closing script tag.
    schema_json = json.dumps(schema, ensure_ascii=False).translate(
        {ord("<"): r"\u003C", ord(">"): r"\u003E", ord("&"): r"\u0026"}
    )
    return render(
        request,
        "landing.html",
        {
            "upcoming": upcoming,
            "archive": published.archive(now)[:5],
            "next_event": future[0] if future else None,
            "residents": Resident.objects.filter(is_published=True),
            "site_url": site_url,
            "schema_json": schema_json,
            "has_schema": bool(future),
        },
    )


@require_safe
def health(request):
    return JsonResponse({"status": "ok"})
