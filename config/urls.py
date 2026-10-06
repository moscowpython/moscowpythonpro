from django.contrib import admin
from django.urls import path

from landing.views import archive, health, index, resident_photo

admin.site.site_header = "Moscow Python / Pro"
admin.site.site_title = "Moscow Python Pro"
admin.site.index_title = "Мероприятия и резиденты"

urlpatterns = [
    path("", index, name="home"),
    path("archive/", archive, name="archive"),
    path("media/residents/<str:filename>", resident_photo, name="resident_photo"),
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
]
