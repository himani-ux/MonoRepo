from __future__ import annotations

import django
import unittest

from django.apps import apps
from django.test import Client
from django.urls import resolve


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-6-url-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "apps.safety",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            ROOT_URLCONF="config.urls",
            ALLOWED_HOSTS=["testserver", "localhost"],
            USE_TZ=True,
        )
    else:
        settings.ROOT_URLCONF = "config.urls"
        settings.ALLOWED_HOSTS = ["testserver", "localhost"]

    if not apps.ready:
        django.setup()


class SafetyUrlIncludeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()
        cls.client = Client()

    def test_api_safety_root_resolves_to_safety_urls(self) -> None:
        match = resolve("/api/safety/")

        self.assertEqual(match.url_name, "api-root")

    def test_api_safety_root_returns_401_without_authorization_header(self) -> None:
        response = self.client.get("/api/safety/")

        self.assertEqual(response.status_code, 401)

    def test_scm_pdf_routes_resolve_to_safety_urls(self) -> None:
        direct_match = resolve("/api/safety/scm/1/pdf/")
        export_match = resolve("/api/safety/export/scm/1/pdf/")

        self.assertEqual(direct_match.url_name, "scm-pdf")
        self.assertEqual(export_match.url_name, "scm-pdf-export")

    def test_incident_pdf_routes_resolve_to_safety_urls(self) -> None:
        direct_match = resolve("/api/safety/incidents/1/pdf/")
        export_match = resolve("/api/safety/export/incident/1/pdf/")

        self.assertEqual(direct_match.url_name, "incident-pdf")
        self.assertEqual(export_match.url_name, "incident-pdf-export")

    def test_near_miss_pdf_routes_resolve_to_safety_urls(self) -> None:
        direct_match = resolve("/api/safety/near-miss/1/pdf/")
        export_match = resolve("/api/safety/export/near-miss/1/pdf/")

        self.assertEqual(direct_match.url_name, "near-miss-pdf")
        self.assertEqual(export_match.url_name, "near-miss-pdf-export")

    def test_soi_pdf_routes_resolve_to_safety_urls(self) -> None:
        direct_match = resolve("/api/safety/soi/1/pdf/")
        summary_match = resolve("/api/safety/soi/1/pdf/summary/")

        self.assertEqual(direct_match.url_name, "soi-pdf")
        self.assertEqual(summary_match.url_name, "soi-pdf-summary")

    def test_auditor_bundle_route_resolves_to_safety_urls(self) -> None:
        match = resolve("/api/safety/export/auditor-bundle/")

        self.assertEqual(match.url_name, "auditor-bundle-export")

    def test_dashboard_composite_route_resolves_to_safety_urls(self) -> None:
        match = resolve("/api/safety/dashboard/composite/")

        self.assertEqual(match.url_name, "dashboard-composite")

    def test_dashboard_analytics_routes_resolve_to_safety_urls(self) -> None:
        heinrich_match = resolve("/api/safety/dashboard/heinrich/")
        repeat_match = resolve("/api/safety/dashboard/repeat-root-cause/")
        pareto_match = resolve("/api/safety/dashboard/pareto/")
        soi_compliance_match = resolve("/api/safety/dashboard/soi-compliance/")
        ca_aging_match = resolve("/api/safety/dashboard/ca-aging/")
        export_match = resolve("/api/safety/dashboard/export/")

        self.assertEqual(heinrich_match.url_name, "dashboard-heinrich")
        self.assertEqual(repeat_match.url_name, "dashboard-repeat-root-cause")
        self.assertEqual(pareto_match.url_name, "dashboard-pareto")
        self.assertEqual(soi_compliance_match.url_name, "dashboard-soi-compliance")
        self.assertEqual(ca_aging_match.url_name, "dashboard-ca-aging")
        self.assertEqual(export_match.url_name, "dashboard-export")

    def test_cross_record_search_route_resolves_to_safety_urls(self) -> None:
        match = resolve("/api/safety/search/")

        self.assertEqual(match.url_name, "search")

    def test_reference_admin_routes_resolve_to_safety_urls(self) -> None:
        mscat_list_match = resolve("/api/safety/reference/mscat/")
        mscat_detail_match = resolve("/api/safety/reference/mscat/10.15/")
        soi_item_detail_match = resolve("/api/safety/reference/soi-items/1/")
        case_study_match = resolve("/api/safety/master/case-studies/")

        self.assertEqual(mscat_list_match.url_name, "reference-mscat-list")
        self.assertEqual(mscat_detail_match.url_name, "reference-mscat-detail")
        self.assertEqual(soi_item_detail_match.url_name, "reference-soi-items-detail")
        self.assertEqual(case_study_match.url_name, "master-case-studies")
