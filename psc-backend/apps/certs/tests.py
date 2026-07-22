from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse
from contextlib import nullcontext
from decimal import Decimal
from django.db import DatabaseError
from io import BytesIO
from pathlib import Path
from rest_framework.test import APIRequestFactory, force_authenticate
import tempfile
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from apps.certs.permissions import can_approve_tracked_item
from apps.certs.serializers.catalog import CatalogRowWriteSerializer
from apps.certs.services.catalog_repository import CatalogRepository
from apps.certs.services.ocr_pipeline import (
    DEFAULT_OCR_ENGINE_NAME,
    OcrEngineOutput,
    OcrFieldCandidate,
    OcrThresholds,
    _paddle_prediction_to_text,
    process_cert_pdf,
)
from apps.certs.services.parsers.base import (
    CLASS_SNAPSHOT_OCR_DET_LIMIT_SIDE_LEN,
    CLASS_SNAPSHOT_OCR_LANGUAGE,
    CLASS_SNAPSHOT_OCR_MAX_PAGES,
    CLASS_SNAPSHOT_OCR_REC_BATCH_SIZE,
    CLASS_SNAPSHOT_OCR_VERSION,
    BaseClassParser,
    ClassSnapshotParseError,
    ExtractedClassSnapshotText,
    extract_pdf_embedded_image_ocr_text,
    extract_pdf_image_ocr_text,
)
from apps.certs.services.parsers.bv import BVClassParser
from apps.certs.services.parsers.kr import KRClassParser
from apps.certs.services.parsers.nk import NKClassParser
from apps.certs.services.pdf_blob_storage import resolve_pdf_blob_path
from apps.certs.services.reconciliation import build_reconciliation_flags, dispatch_parser_anomaly_notifications
from apps.certs.services.notification_dispatcher import CertNotificationRecipient
from apps.certs.services.tracked_item_repository import TrackedItemRepository
from apps.certs.serializers.tracked_item import TrackedItemWriteSerializer
from apps.certs.views import snapshot_views


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


class ClassSnapshotUploadParsingTests(SimpleTestCase):
    def test_upload_immediately_reparses_and_returns_run_ready_snapshot(self):
        vessel_id = "11111111-1111-1111-1111-111111111111"
        snapshot_id = "22222222-2222-2222-2222-222222222222"
        run_id = "33333333-3333-3333-3333-333333333333"
        blob_id = "44444444-4444-4444-4444-444444444444"
        user = SimpleNamespace(
            is_authenticated=True,
            user_type="OFFICE",
            role="DPA",
            form_ids=["CERT_F_003"],
            process_ids=["CERT_P_001"],
            has_global_vessel_access=True,
        )
        request = APIRequestFactory().post(
            "/api/certs/class-snapshots/",
            data={
                "vesselId": vessel_id,
                "classSociety": "NK",
                "printedOnDate": "2026-07-20",
                "file": SimpleUploadedFile("class-status.pdf", b"%PDF-1.4\n%", content_type="application/pdf"),
            },
            format="multipart",
        )
        force_authenticate(request, user=user)
        pending_snapshot = _class_snapshot_row(
            snapshot_id=snapshot_id,
            vessel_id=vessel_id,
            blob_id=blob_id,
            parse_status="pending",
            reconciliation_run_id=None,
        )
        parsed_snapshot = _class_snapshot_row(
            snapshot_id=snapshot_id,
            vessel_id=vessel_id,
            blob_id=blob_id,
            parse_status="success",
            reconciliation_run_id=run_id,
            parser_version="nk-pdfplumber-v1",
        )

        with (
            patch(
                "apps.certs.views.snapshot_views.save_uploaded_class_snapshot_pdf",
                return_value={"relative_path": "certs/vessels/test/class-status.pdf", "filename": "class-status.pdf", "sha256": "sha", "size": 10},
            ),
            patch("apps.certs.views.snapshot_views.resolve_actor_id", return_value="actor-1"),
            patch.object(snapshot_views.pdf_repository, "create_snapshot_blob", return_value={"blob_id": blob_id}),
            patch.object(snapshot_views.repository, "create_snapshot", return_value=pending_snapshot) as create_snapshot,
            patch("apps.certs.views.snapshot_views.run_class_snapshot_parser", return_value=(parsed_snapshot, {"run_id": run_id})) as parser_worker,
            patch("apps.certs.views.snapshot_views.record_audit_event"),
            patch("apps.certs.views.snapshot_views.transaction.atomic", return_value=nullcontext()),
        ):
            response = snapshot_views.ClassSnapshotListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["parseStatus"], "success")
        self.assertEqual(response.data["reconciliationRunId"], run_id)
        create_snapshot.assert_called_once()
        parser_worker.assert_called_once_with(snapshot_id, repository=snapshot_views.repository)


class ClassSnapshotParserAndReconciliationSmokeTests(SimpleTestCase):
    def test_class_snapshot_parser_reports_ocr_fallback_without_readable_text(self):
        parser = _NoopClassParser()

        with (
            patch("apps.certs.services.parsers.base.extract_pdf_text", return_value=ExtractedClassSnapshotText("", 19, "paddleocr_fallback")),
            self.assertRaisesRegex(ClassSnapshotParseError, "OCR fallback read no text"),
        ):
            parser.parse("image-only-class-status.pdf")

    def test_class_snapshot_parser_uses_ocr_fallback_when_pdf_has_no_text_layer(self):
        ocr_text = """KOREAN REGISTER
Ship Name EAST AYUTTHAYA Work ID VANS004726
Class No. 1000010 IMO No. 9584293
Certificates
Class Certificates
Cargo Gear(CG2) Certificate CG2 Full 2026-02-27 2031-02-26 CL26001506350
Statutory Certificates or Documents of Compliance issued by KR
Load Line Certificate ILL Full 2025-08-11 2030-07-11 0N25015926559
"""

        with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
            with (
                patch("pdfplumber.open", return_value=_EmptyPdfPlumberDocument(page_count=3)),
                patch("apps.certs.services.parsers.base.extract_pdf_image_ocr_text", return_value=ocr_text),
            ):
                parsed = KRClassParser().parse(pdf_file.name)

        self.assertEqual(parsed.parse_status, "success")
        self.assertEqual(parsed.payload["source"], "ocr_text")
        self.assertEqual(parsed.payload["text_extraction"]["engine"], "paddleocr_fallback")
        self.assertEqual(parsed.payload["vessel"]["name"], "EAST AYUTTHAYA")
        self.assertEqual(parsed.payload["vessel"]["imo"], "9584293")
        self.assertGreaterEqual(len(parsed.payload["rows"]), 2)

    def test_class_snapshot_ocr_fallback_uses_paddleocr_page_cap(self):
        fake_engine = _FakeOcrEngine(
            OcrEngineOutput(
                raw_text="KOREAN REGISTER\nIMO No. 9584293",
                mean_confidence=0.93,
                fields={},
            )
        )

        with patch("apps.certs.services.parsers.base.PaddleOcrEngine", return_value=fake_engine) as engine_class:
            text = extract_pdf_image_ocr_text("image-only-class-status.pdf")

        engine_class.assert_called_once_with(**_class_snapshot_ocr_kwargs())
        self.assertIn("KOREAN REGISTER", text)

    def test_class_snapshot_ocr_fallback_reads_embedded_page_images(self):
        page_image = _png_bytes(width=1273, height=1800)
        logo_image = _png_bytes(width=583, height=73)
        fake_reader = _FakePdfReader([_FakePdfPage([_FakePdfImage(logo_image), _FakePdfImage(page_image)])])
        fake_engine = _FakeClassSnapshotOcrEngine("KOREAN REGISTER\nIMO No. 9584293")

        with (
            patch("PyPDF2.PdfReader", return_value=fake_reader),
            patch("apps.certs.services.parsers.base.PaddleOcrEngine", return_value=fake_engine) as engine_class,
        ):
            text = extract_pdf_embedded_image_ocr_text("image-only-class-status.pdf")

        engine_class.assert_called_once_with(**_class_snapshot_ocr_kwargs())
        self.assertEqual(fake_engine.calls, 1)
        self.assertIn("--- PAGE 1 OCR ---", text)
        self.assertIn("IMO No. 9584293", text)

    def test_class_snapshot_embedded_ocr_can_limit_pages(self):
        first_page = _png_bytes(width=1273, height=1800)
        second_page = _png_bytes(width=1273, height=1800)
        fake_reader = _FakePdfReader(
            [
                _FakePdfPage([_FakePdfImage(first_page)]),
                _FakePdfPage([_FakePdfImage(second_page)]),
            ]
        )
        fake_engine = _FakeClassSnapshotOcrEngine("Certificate row")

        with (
            patch("PyPDF2.PdfReader", return_value=fake_reader),
            patch("apps.certs.services.parsers.base.PaddleOcrEngine", return_value=fake_engine),
        ):
            text = extract_pdf_embedded_image_ocr_text("image-only-class-status.pdf", ocr_page_numbers=(2,))

        self.assertEqual(fake_engine.calls, 1)
        self.assertNotIn("--- PAGE 1 OCR ---", text)
        self.assertIn("--- PAGE 2 OCR ---", text)

    def test_process_cert_pdf_defaults_to_paddleocr_payload_contract(self):
        output = OcrEngineOutput(
            raw_text=(
                "Certificate Type: Certificate of Classification\n"
                "Vessel Name: EAST AYUTTHAYA\n"
                "IMO No. 9584293\n"
                "Issue Date: 01/07/2026\n"
                "Expiry Date: 01/07/2031\n"
                "Certificate No.: KR-001\n"
                "Place of Issue: Busan\n"
                "Issuing Authority: Korean Register\n"
            ),
            mean_confidence=0.92,
            fields={"certificate_number": OcrFieldCandidate("KR-001", 0.94)},
        )

        with patch("apps.certs.services.ocr_pipeline.PaddleOcrEngine", return_value=_FakeOcrEngine(output)) as engine_class:
            payload = process_cert_pdf(
                "certificate.png",
                thresholds=OcrThresholds(office_auto_accept=0.80, vessel_auto_accept=0.85, manual_floor=0.60),
            )

        engine_class.assert_called_once_with()
        self.assertEqual(payload["engine"], DEFAULT_OCR_ENGINE_NAME)
        self.assertEqual(payload["status"], "processed")
        self.assertEqual(payload["fields"]["certificate_number"]["value"], "KR-001")
        self.assertEqual(payload["fields"]["imo_number"]["value"], "9584293")

    def test_paddleocr_v3_prediction_result_is_flattened_to_text_and_confidence(self):
        text, confidence = _paddle_prediction_to_text(
            [
                {
                    "res": {
                        "rec_texts": ["KOREAN REGISTER", "IMO No. 9584293"],
                        "rec_scores": [0.96, 0.92],
                    }
                }
            ]
        )

        self.assertEqual(text, "KOREAN REGISTER\nIMO No. 9584293")
        self.assertAlmostEqual(confidence, 0.94)

    def test_paddleocr_prediction_reconstructs_table_rows_from_boxes(self):
        text, confidence = _paddle_prediction_to_text(
            [
                {
                    "res": {
                        "rec_texts": [
                            "Classification Certificate(Full)",
                            "CC",
                            "Full",
                            "2025-08-11",
                            "2030-07-11",
                            "Annual Survey",
                            "2026-07-11",
                        ],
                        "rec_scores": [0.96, 0.95, 0.97, 0.98, 0.99, 0.94, 0.93],
                        "rec_boxes": _TruthlessBoxes(
                            [
                                [Decimal("10"), Decimal("10"), Decimal("260"), Decimal("30")],
                                [Decimal("300"), Decimal("11"), Decimal("330"), Decimal("30")],
                                [Decimal("360"), Decimal("10"), Decimal("410"), Decimal("30")],
                                [Decimal("450"), Decimal("10"), Decimal("540"), Decimal("30")],
                                [Decimal("570"), Decimal("10"), Decimal("660"), Decimal("30")],
                                [Decimal("10"), Decimal("55"), Decimal("120"), Decimal("75")],
                                [Decimal("450"), Decimal("55"), Decimal("540"), Decimal("75")],
                            ]
                        ),
                    }
                }
            ]
        )

        self.assertIn("Classification Certificate(Full) CC Full 2025-08-11 2030-07-11", text)
        self.assertIn("Annual Survey 2026-07-11", text)
        self.assertAlmostEqual(confidence, 0.96, places=2)

    def test_class_parser_text_smoke_covers_supported_societies(self):
        samples = {
            "NK": (
                NKClassParser(),
                """NK-SHIPS Information Service
Name of Ship: TEST VESSEL Class No. : NK 123456 IMO No. : 1234567
Printed on 01.Jan.2026
Survey Status:: Class
Hull Annual Survey 01 Jan 2027
Condition & Note
""",
            ),
            "KR": (
                KRClassParser(),
                """VESSEL STATUS FOR SHIP'S OWNER TEST VESSEL Class No : 98765 IMO No : 1234567 Printed on 01-Jan-2026
Certificates
International Oil Pollution Prevention Certificate IOPP Full 2024-01-01 2029-01-01
Class Surveys
Ship Name Work ID
Hull Annual Survey 2025-01-01 2026-01-01
""",
            ),
            "BV": (
                BVClassParser(),
                """Ship name: TEST VESSEL BV Nr BV123 IMO Number: 1234567 Generated on 1 Jan 2026
Classification Surveys
Hull Annual Survey 1 Jan 2025 1 Jan 2026
Conditions of Class / Statutory Recommendations
None
""",
            ),
        }

        for society, (parser, text) in samples.items():
            with self.subTest(society=society):
                payload = parser.parse_text(text, page_count=1)
                self.assertEqual(payload["class_society"], society)
                self.assertGreaterEqual(len(payload["rows"]), 1)

    def test_kr_parser_accepts_ocr_table_rows(self):
        payload = KRClassParser().parse_text(
            """Ship Name EAST AYUTTHAYA Work ID VANS004726
Class No. 1000010 IMO No. 9584293
Certificates
Class Certificates
Cargo Ship Safety Construction Certificate Sc Full 2025-08-11 2030-07-11 CN25015925557
Loading Instrument Certificate LI Permanence 2025-08-11 CL25004894584
Vessel General Permit VGP 2025-08-11 CN25015890568
Class Surveys
Annual Survey 2026-07-11 2026-04-11-2026-10-11
Hull Annual Survey 2025-01-01 2026-01-01
""",
            page_count=19,
        )

        rows_by_code = {row["class_code_or_name"]: row for row in payload["rows"]}
        self.assertEqual(rows_by_code["SC"]["expiry_date"], "2030-07-11")
        self.assertNotIn("expiry_date", rows_by_code["LI"])
        self.assertEqual(rows_by_code["VGP"]["issue_date"], "2025-08-11")

        annual = next(row for row in payload["rows"] if row["raw_text"].startswith("Annual Survey"))
        self.assertNotIn("last_done_date", annual)
        self.assertEqual(annual["next_due_date"], "2026-07-11")
        hull = next(row for row in payload["rows"] if row["raw_text"].startswith("Hull Annual Survey"))
        self.assertEqual(hull["last_done_date"], "2025-01-01")
        self.assertEqual(hull["next_due_date"], "2026-01-01")

    def test_reconciliation_buckets_snapshot_rows_against_tracked_items(self):
        result = build_reconciliation_flags(
            parsed_payload={
                "rows": [
                    {"class_code_or_name": "IOPP", "certificate_number": "C-001", "expiry_date": "2029-01-01", "confidence": 1.0},
                    {"class_code_or_name": "LOADLINE", "certificate_number": "C-002", "expiry_date": "2028-01-01", "confidence": 1.0},
                    {"class_code_or_name": "UNKNOWN", "confidence": 1.0},
                    {"class_code_or_name": "LOWCONF", "confidence": 0.5},
                    {"class_code_or_name": "STCROW", "type": "STC", "confidence": 1.0},
                    {"class_code_or_name": "POSTROW", "status": "POSTPONED", "postponed_until": "2027-01-01", "confidence": 1.0},
                ]
            },
            tracked_items=[
                {"tracked_item_id": "ti-1", "catalog_id": "cat-1", "catalog_is_class_tracked": True, "certificate_number": "C-001", "expiry_date": "2029-01-01"},
                {"tracked_item_id": "ti-2", "catalog_id": "cat-2", "catalog_is_class_tracked": True, "certificate_number": "C-002", "expiry_date": "2029-01-01"},
                {"tracked_item_id": "ti-3", "catalog_id": "cat-3", "catalog_is_class_tracked": True},
                {"tracked_item_id": "ti-4", "catalog_id": "cat-4", "catalog_is_class_tracked": True},
                {"tracked_item_id": "ti-5", "catalog_id": "cat-5", "catalog_is_class_tracked": True},
            ],
            mappings=[
                {"class_code_or_name": "IOPP", "catalog_id": "cat-1", "version": 1},
                {"class_code_or_name": "LOADLINE", "catalog_id": "cat-2", "version": 1},
                {"class_code_or_name": "STCROW", "catalog_id": "cat-3", "version": 1},
                {"class_code_or_name": "POSTROW", "catalog_id": "cat-4", "version": 1},
            ],
        )

        self.assertEqual(
            result.counts,
            {
                "matches_count": 1,
                "mismatches_count": 1,
                "missing_in_catalog_count": 1,
                "missing_in_class_count": 1,
                "conditional_stc_detected_count": 1,
                "extended_postponed_detected_count": 1,
                "unmapped_low_confidence_count": 1,
            },
        )

    def test_parser_anomaly_notification_schema_failure_does_not_abort_reconciliation(self):
        result = dispatch_parser_anomaly_notifications(
            run={"run_id": "run-1", "vessel_id": "vessel-1", "vessel_name": "MV Test", "class_society": "KR"},
            anomaly_breaches=[{"type": "parse_duration", "severity": "critical"}],
            flags=[],
            dispatcher=_FailingNotificationDispatcher(),
            candidate_recipients=[
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
                CertNotificationRecipient(user_id="tech-1", role="Technical Superintendent", side="office"),
            ],
        )

        self.assertFalse(result["dispatched"])
        self.assertEqual(result["reason"], "notification_dispatch_failed")
        self.assertEqual(result["notificationsSent"], [])


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


def _class_snapshot_row(
    *,
    snapshot_id: str,
    vessel_id: str,
    blob_id: str,
    parse_status: str,
    reconciliation_run_id: str | None,
    parser_version: str = "pending-parser-v1",
) -> dict[str, object]:
    return {
        "snapshot_id": snapshot_id,
        "vessel_id": vessel_id,
        "vessel_name": "MV Test",
        "imo_number": "1234567",
        "class_society": "NK",
        "pdf_blob_id": blob_id,
        "filename": "class-status.pdf",
        "content_size_bytes": 10,
        "printed_on_date": "2026-07-20",
        "uploaded_by": "actor-1",
        "uploaded_at": "2026-07-20T10:00:00Z",
        "parser_version": parser_version,
        "parse_status": parse_status,
        "parse_started_at": None,
        "parse_completed_at": "2026-07-20T10:00:05Z" if parse_status != "pending" else None,
        "parser_timeout": False,
        "retry_count": 0,
        "parsed_payload_json": None,
        "parsed_payload_schema_version": 1,
        "reconciliation_run_id": reconciliation_run_id,
        "upload_sha256": "sha",
        "superseded_user_error": False,
    }


class _NoopClassParser(BaseClassParser):
    def parse_text(self, text: str, *, page_count: int) -> dict[str, object]:
        return {"rows": [], "schema_version": 1}


class _EmptyPdfPlumberDocument:
    def __init__(self, *, page_count: int):
        self.pages = [_EmptyPdfPlumberPage() for _ in range(page_count)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _EmptyPdfPlumberPage:
    def extract_text(self, **_kwargs):
        return ""


class _FailingNotificationDispatcher:
    def dispatch(self, **_kwargs):
        raise DatabaseError("Invalid column name 'module_code'.")


class _FakeOcrEngine:
    engine_name = DEFAULT_OCR_ENGINE_NAME

    def __init__(self, output: OcrEngineOutput):
        self.output = output

    def extract(self, _source_path):
        return self.output


class _FakeClassSnapshotOcrEngine:
    def __init__(self, text: str):
        self.text = text
        self.calls = 0

    def extract_image_text(self, _source_path):
        self.calls += 1
        return self.text, 0.95


class _FakePdfReader:
    def __init__(self, pages):
        self.pages = pages


class _FakePdfPage:
    def __init__(self, images):
        self._images = images

    def get(self, key):
        if key == "/Resources":
            return {"/XObject": _FakePdfXObjects(self._images)}
        return None


class _FakePdfXObjects:
    def __init__(self, images):
        self._images = images

    def get_object(self):
        return {f"/X{index}": image for index, image in enumerate(self._images, start=1)}


class _FakePdfImage:
    def __init__(self, content: bytes):
        self._content = content

    def get_object(self):
        return self

    def get(self, key):
        if key == "/Subtype":
            return "/Image"
        return None

    def get_data(self):
        return self._content


class _TruthlessBoxes(list):
    def __bool__(self):
        raise ValueError("array truth value is ambiguous")


def _png_bytes(*, width: int, height: int) -> bytes:
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def _class_snapshot_ocr_kwargs() -> dict[str, object]:
    return {
        "language": CLASS_SNAPSHOT_OCR_LANGUAGE,
        "max_pdf_pages": CLASS_SNAPSHOT_OCR_MAX_PAGES,
        "ocr_version": CLASS_SNAPSHOT_OCR_VERSION,
        "text_det_limit_side_len": CLASS_SNAPSHOT_OCR_DET_LIMIT_SIDE_LEN,
        "text_recognition_batch_size": CLASS_SNAPSHOT_OCR_REC_BATCH_SIZE,
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
