from django.urls import include, path


urlpatterns = [
    path("api/safety/", include("apps.safety.urls")),
]
