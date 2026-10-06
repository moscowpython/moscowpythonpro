import json

from django.conf import settings
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
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
        "url": f"{site_url}{event.get_absolute_url()}",
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


def public_origin(request):
    return (
        request.build_absolute_uri("/").rstrip("/")
        if settings.SITE_URL_FROM_REQUEST
        else settings.SITE_URL
    )


@require_safe
def index(request):
    site_url = public_origin(request)
    now = timezone.now()
    published = Event.objects.published()
    upcoming = list(published.upcoming(now))
    future = [event for event in upcoming if event.starts_at > now]
    schema = {
        "@context": "https://schema.org",
        "@graph": [event_schema(e, site_url) for e in future],
    }
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
def archive(request):
    page = Paginator(Event.objects.published().archive(timezone.now()), 20).get_page(
        request.GET.get("page")
    )
    origin = public_origin(request)
    return render(
        request,
        "archive.html",
        {
            "page": page,
            "site_url": origin,
            "canonical_url": f"{origin}/archive/"
            + (f"?page={page.number}" if page.number > 1 else ""),
            "page_title": "Прошедшие мероприятия — Moscow Python Pro",
            "page_description": "Архив оффлайн-встреч Moscow Python Pro: темы, форматы и спикеры прошедших мероприятий.",
        },
    )


@require_safe
def event_detail(request, pk):
    event = get_object_or_404(Event.objects.published(), pk=pk)
    origin = public_origin(request)
    now = timezone.now()
    schema = {"@context": "https://schema.org", **event_schema(event, origin)}
    schema_json = json.dumps(schema, ensure_ascii=False).translate(
        {ord("<"): r"\u003C", ord(">"): r"\u003E", ord("&"): r"\u0026"}
    )
    return render(
        request,
        "event_detail.html",
        {
            "event": event,
            "is_past": event.status_at(now) == "Прошедшее",
            "site_url": origin,
            "canonical_url": f"{origin}{event.get_absolute_url()}",
            "page_title": f"{event.title} — Moscow Python Pro",
            "page_description": event.short_description or event.title,
            "has_schema": True,
            "schema_json": schema_json,
        },
    )


@require_safe
def resident_photo(request, filename):
    resident = get_object_or_404(Resident, photo=f"residents/{filename}")
    if not resident.photo or (not resident.is_published and not request.user.is_staff):
        raise Http404
    try:
        photo = resident.photo.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    response = FileResponse(photo, content_type="image/webp")
    response["Cache-Control"] = "private, no-cache"
    return response


@require_safe
def health(request):
    return JsonResponse({"status": "ok"})
