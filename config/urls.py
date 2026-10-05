from django.contrib import admin
from django.urls import path

from landing.views import health, index

admin.site.site_header = "Moscow Python / Pro"
admin.site.site_title = "Moscow Python Pro"
admin.site.index_title = "Мероприятия и резиденты"

urlpatterns = [
    path("", index, name="home"),
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
]
