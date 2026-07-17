from django.conf import settings
from django.test import SimpleTestCase
from django.urls import resolve, reverse
from unittest import TestCase
from unittest.mock import patch

from apps.certs.serializers.catalog import CatalogRowWriteSerializer
from apps.certs.services.catalog_repository import CatalogRepository
from apps.certs.serializers.tracked_item import TrackedItemWriteSerializer


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


class CatalogRowSubmissionScopeTests(SimpleTestCase):
    def test_catalog_row_create_rejects_master_only_under_all_rank_policy(self):
        serializer = CatalogRowWriteSerializer(
            data=_catalog_row_payload("master_only"),
            context={"is_create": True},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("submissionScope", serializer.errors)

    def test_catalog_row_create_accepts_all_rank_policy(self):
        serializer = CatalogRowWriteSerializer(
            data=_catalog_row_payload("all_ranks_with_approval"),
            context={"is_create": True},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)


def _catalog_row_payload(submission_scope: str) -> dict[str, object]:
    return {
        "canonicalCode": "TEST-CATALOG-ROW",
        "sectionId": 2,
        "displayName": "Test Catalog Row",
        "printSectionLabel": "Statutory & Flag",
        "validityType": "full",
        "issuingAuthorityType": "flag",
        "submissionScope": submission_scope,
    }


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


class TrackedItemMetadataSerializerTests(SimpleTestCase):
    def test_partial_metadata_correction_payload_is_valid(self):
        serializer = TrackedItemWriteSerializer(
            data={
                "certificateNumber": "CERT-2026-001",
                "issuingAuthority": "ClassNK",
                "placeOfIssue": "Singapore",
                "issueDate": "2026-07-01",
                "expiryDate": "2027-07-01",
                "reason": "Metadata corrected after OCR review.",
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
