"""Safety-only URLConf for handover-era Safety tests."""

from django.urls import include, path


urlpatterns = [
    path("api/safety/", include("apps.safety.urls")),
]
