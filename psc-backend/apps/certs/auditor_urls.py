from __future__ import annotations

from django.urls import path

from apps.certs.views import (
    AuditorCertDetailView,
    AuditorPrintView,
    AuditorSignupView,
    AuditorVesselCertListView,
    AuditorVesselListView,
)


app_name = "certs_auditor"

urlpatterns = [
    path("signup/<path:token>/", AuditorSignupView.as_view(), name="signup"),
    path("<path:grant_token>/vessels/<str:imo>/certs/", AuditorVesselCertListView.as_view(), name="vessel-certs"),
    path("<path:grant_token>/vessels/", AuditorVesselListView.as_view(), name="vessels"),
    path("<path:grant_token>/cert/<uuid:cert_id>/", AuditorCertDetailView.as_view(), name="cert-detail"),
    path("<path:grant_token>/print/", AuditorPrintView.as_view(), name="print"),
]
