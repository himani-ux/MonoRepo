from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from apps.certs.permissions import can_approve_tracked_item
from apps.certs.serializers.catalog import CatalogRowWriteSerializer
from apps.certs.services.catalog_repository import CatalogRepository
from apps.certs.services.pdf_blob_storage import resolve_pdf_blob_path
from apps.certs.services.tracked_item_repository import TrackedItemRepository
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


class TrackedItemRepositoryFilterTests(TestCase):
    def test_list_items_can_filter_by_approval_state(self):
        cursor = _FakeTrackedItemCursor()

        with patch("apps.certs.services.tracked_item_repository.connection.cursor", return_value=cursor):
            page = TrackedItemRepository().list_items(approval_state="pending_master_approval")

        self.assertEqual(page.count, 0)
        self.assertIn("t.approval_state = %s", cursor.executed[0][0])
        self.assertIn("t.approval_state = %s", cursor.executed[1][0])
        self.assertEqual(cursor.executed[0][1], ["pending_master_approval"])


class TrackedItemApprovalAuthorityTests(SimpleTestCase):
    def test_dpa_can_approve_when_vessel_access_is_global(self):
        user = SimpleNamespace(user_type="OFFICE", role="DPA", has_global_vessel_access=True)

        self.assertTrue(can_approve_tracked_item(user, {"vessel_id": "VESSEL-1"}))

    def test_pic_can_approve_when_vessel_is_assigned(self):
        user = SimpleNamespace(user_type="OFFICE", role="OFFICE_PIC", vessel_ids=["VESSEL-1"])

        self.assertTrue(can_approve_tracked_item(user, {"vessel_id": "VESSEL-1"}))

    def test_non_approval_office_role_cannot_approve(self):
        user = SimpleNamespace(user_type="OFFICE", role="CHIEF ACCOUNTING OFFICER", has_global_vessel_access=True)

        self.assertFalse(can_approve_tracked_item(user, {"vessel_id": "VESSEL-1"}))


class PdfBlobStoragePathTests(SimpleTestCase):
    def test_resolves_pdf_blob_path_inside_upload_root(self):
        with tempfile.TemporaryDirectory() as upload_root, override_settings(UPLOAD_BASE_PATH=upload_root):
            resolved = resolve_pdf_blob_path({"blob_storage_path": "certs/vessel-1/class.pdf"})

        self.assertEqual(resolved, Path(upload_root).resolve() / "certs" / "vessel-1" / "class.pdf")

    def test_rejects_pdf_blob_path_outside_upload_root(self):
        with tempfile.TemporaryDirectory() as upload_root, override_settings(UPLOAD_BASE_PATH=upload_root):
            with self.assertRaises(SuspiciousFileOperation):
                resolve_pdf_blob_path({"blob_storage_path": "../outside.pdf"})


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


class _FakeTrackedItemCursor:
    def __init__(self):
        self.executed = []
        self.description = [("tracked_item_id",)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, list(params or [])))

    def fetchone(self):
        return (0,)

    def fetchall(self):
        return []


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
