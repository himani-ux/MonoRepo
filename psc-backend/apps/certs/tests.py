from django.conf import settings
from django.test import SimpleTestCase
from django.urls import resolve, reverse
from unittest import TestCase
from unittest.mock import patch

from apps.certs.services.catalog_repository import CatalogRepository


class CertsAppRegistrationTests(SimpleTestCase):
    def test_certs_app_is_registered(self):
        self.assertIn("apps.certs", settings.INSTALLED_APPS)

    def test_certs_routes_are_mounted(self):
        self.assertEqual(reverse("certs:health"), "/api/certs/health/")
        self.assertEqual(resolve("/api/certs/health/").url_name, "health")
        self.assertEqual(
            reverse("certs-auditor:signup", kwargs={"token": "sample"}),
            "/api/auditor/signup/sample/",
        )


class CatalogRepositoryPaginationTests(TestCase):
    def test_list_rows_uses_offset_fetch_when_page_requested(self):
        cursor = _FakeCatalogCursor()

        with patch("apps.certs.services.catalog_repository.connection.cursor", return_value=cursor):
            page = CatalogRepository().list_rows(is_active=True, page=2, page_size=25)

        self.assertEqual(page.count, 123)
        self.assertEqual(page.page, 2)
        self.assertEqual(page.page_size, 25)
        self.assertEqual(page.results, [{"catalog_id": "catalog-1"}])
        self.assertIn("OFFSET %s ROWS FETCH NEXT %s ROWS ONLY", cursor.executed[1][0])
        self.assertEqual(cursor.executed[1][1][-2:], [25, 25])


class _FakeCatalogCursor:
    def __init__(self):
        self.executed = []
        self.description = [("catalog_id",)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params or [])))

    def fetchone(self):
        return (123,)

    def fetchall(self):
        return [("catalog-1",)]
