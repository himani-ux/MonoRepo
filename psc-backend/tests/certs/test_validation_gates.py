from __future__ import annotations

import os
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from apps.certs.services.validation_gates import validate_onboarding_batch
from apps.certs.services.idempotency import analyze_pdf_idempotency
from apps.certs.services.onboarding_repository import OnboardingRepository


def field(value, **overrides):
    payload = {"value": value, "confidence": 0.9, "mode": "auto_accept", "required": False}
    payload.update(overrides)
    return payload


def complete_fields(**overrides):
    values = {
        "certificate_type": field("International Oil Pollution Prevention Certificate"),
        "issuing_authority": field("Panama Maritime Authority"),
        "vessel_name": field("KSM Fortitude"),
        "imo_number": field("9876543"),
        "issue_date": field("2026-01-01"),
        "expiry_date": field("2031-01-01"),
        "certificate_number": field("IOPP-001"),
        "place_of_issue": field("Panama"),
        "validity_type": field("full"),
        "issuer_type": field("flag"),
        "catalog_id": field("catalog-iopp"),
    }
    values.update(overrides)
    return values


def ocr_blob(**overrides):
    blob_id = overrides.pop("blob_id", str(uuid.uuid4()))
    fields = overrides.pop("fields", complete_fields())
    row = {
        "blob_id": blob_id,
        "filename": f"{blob_id}.pdf",
        "ocr_payload_json": {"status": "processed", "fields": fields},
        "tracked_item": {"pdf_missing": False, "catalog_id": fields.get("catalog_id", {}).get("value")},
    }
    row.update(overrides)
    return row


class CertValidationGateTests(unittest.TestCase):
    def test_idempotency_silently_skips_same_pdf_hash(self) -> None:
        result = analyze_pdf_idempotency(
            pdfs=[
                ocr_blob(
                    blob_id="new-blob",
                    content_sha256="a" * 64,
                    fields=complete_fields(certificate_number=field("IOPP-001")),
                )
            ],
            existing_by_certificate_number={
                "IOPP-001": [
                    {
                        "blob_id": "existing-blob",
                        "tracked_item_id": "tracked-1",
                        "content_sha256": "a" * 64,
                    }
                ]
            },
        )

        self.assertTrue(result.can_commit)
        self.assertEqual(result.blocks, [])
        self.assertEqual(result.skipped_duplicates[0]["blobId"], "new-blob")
        self.assertEqual(result.skipped_duplicates[0]["existingBlobId"], "existing-blob")
        self.assertEqual(result.superseded_pdfs, [])

    def test_idempotency_requires_confirmation_for_same_number_different_hash(self) -> None:
        result = analyze_pdf_idempotency(
            pdfs=[
                ocr_blob(
                    blob_id="new-blob",
                    content_sha256="b" * 64,
                    fields=complete_fields(certificate_number=field("IOPP-001")),
                )
            ],
            existing_by_certificate_number={
                "IOPP-001": [
                    {
                        "blob_id": "existing-blob",
                        "tracked_item_id": "tracked-1",
                        "content_sha256": "a" * 64,
                    }
                ]
            },
        )

        self.assertFalse(result.can_commit)
        self.assertEqual(result.blocks[0]["code"], "supersede_confirmation_required")
        self.assertEqual(result.blocks[0]["blobId"], "new-blob")
        self.assertEqual(result.blocks[0]["value"], "existing-blob")

        confirmed = analyze_pdf_idempotency(
            pdfs=[
                ocr_blob(
                    blob_id="new-blob",
                    content_sha256="b" * 64,
                    fields=complete_fields(certificate_number=field("IOPP-001")),
                )
            ],
            existing_by_certificate_number={
                "IOPP-001": [
                    {
                        "blob_id": "existing-blob",
                        "tracked_item_id": "tracked-1",
                        "content_sha256": "a" * 64,
                    }
                ]
            },
            supersede_decisions=[{"blobId": "new-blob", "existingBlobId": "existing-blob", "confirm": True}],
        )

        self.assertTrue(confirmed.can_commit)
        self.assertEqual(confirmed.blocks, [])
        self.assertEqual(confirmed.superseded_pdfs[0]["existingBlobId"], "existing-blob")

    def test_validation_blocks_match_d_cert_116_matrix(self) -> None:
        future_issue = (date.today() + timedelta(days=7)).isoformat()
        pdfs = [
            ocr_blob(fields=complete_fields(certificate_type=field(None))),
            ocr_blob(
                fields=complete_fields(
                    certificate_number=field(None),
                    certificate_number_bypass=field(True),
                    certificate_number_bypass_reason=field("Too short"),
                )
            ),
            ocr_blob(fields=complete_fields(imo_number=field("0000000"))),
            ocr_blob(fields=complete_fields(issue_date=field(future_issue))),
            ocr_blob(fields=complete_fields(validity_type=field("unknown"))),
            ocr_blob(fields=complete_fields(certificate_number=field("DUP-001"))),
            ocr_blob(fields=complete_fields(certificate_number=field("DUP-001"))),
        ]

        result = validate_onboarding_batch(
            batch={"batch_id": "batch-1"},
            vessel={"vessel_id": "vessel-1", "imo_number": "9876543"},
            pdfs=pdfs,
        )

        codes = {entry["code"] for entry in result.blocks}
        self.assertIn("required_field_missing", codes)
        self.assertIn("cert_number_bypass_reason_missing", codes)
        self.assertIn("ocr_imo_unresolved", codes)
        self.assertIn("issue_date_future", codes)
        self.assertIn("validity_type_unknown", codes)
        self.assertIn("duplicate_cert_number_in_batch", codes)
        self.assertFalse(result.can_commit)

    def test_validation_warns_match_d_cert_116_matrix_and_allow_ack_commit(self) -> None:
        expired_date = (date.today() - timedelta(days=30)).isoformat()
        pdfs = [
            ocr_blob(fields=complete_fields(issuer_type=field("unknown"), expiry_date=field(expired_date))),
            ocr_blob(fields=complete_fields(catalog_id=field("catalog-duplicate"), certificate_number=field("CAT-001"))),
            ocr_blob(fields=complete_fields(catalog_id=field("catalog-duplicate"), certificate_number=field("CAT-002"))),
            ocr_blob(fields=complete_fields(certificate_number=field("MISS-001")), tracked_item={"pdf_missing": True}),
        ]

        result = validate_onboarding_batch(
            batch={"batch_id": "batch-1"},
            vessel={"vessel_id": "vessel-1", "imo_number": "9876543"},
            pdfs=pdfs,
        )

        codes = {entry["code"] for entry in result.warns}
        self.assertIn("issuer_type_unknown", codes)
        self.assertIn("expiry_date_in_past", codes)
        self.assertIn("duplicate_catalog_for_vessel", codes)
        self.assertIn("pdf_missing", codes)
        self.assertTrue(result.can_commit)
        self.assertTrue(result.requires_warning_ack)

    @patch("apps.certs.services.onboarding_repository.connection")
    def test_repository_persists_validation_and_marks_commit_pending(self, connection) -> None:
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.description = [
            ("batch_id",),
            ("vessel_id",),
            ("onboarding_session_id",),
            ("pdf_blob_ids_json",),
            ("pdf_count",),
            ("status",),
            ("created_at",),
            ("created_by",),
            ("ocr_completed_at",),
            ("review_started_at",),
            ("committed_at",),
            ("committed_by",),
            ("cancelled_at",),
            ("cancelled_by",),
            ("validation_blocks_json",),
            ("validation_warns_json",),
            ("report_csv_blob_id",),
        ]
        cursor.fetchall.return_value = [(
            "batch-1",
            "vessel-1",
            "session-1",
            '["blob-1"]',
            1,
            "commit_pending",
            "2026-06-26T09:00:00Z",
            "dpa-1",
            "2026-06-26T09:05:00Z",
            "2026-06-26T09:10:00Z",
            None,
            None,
            None,
            None,
            '[{"code":"required_field_missing"}]',
            "[]",
            None,
        )]

        repository = OnboardingRepository()
        batch = repository.persist_batch_validation(
            "batch-1",
            blocks=[{"code": "required_field_missing"}],
            warns=[],
        )

        self.assertEqual(batch["status"], "commit_pending")
        self.assertEqual(batch["validation_blocks_json"], '[{"code":"required_field_missing"}]')
        self.assertIn("validation_blocks_json", cursor.execute.call_args_list[0].args[0])

    @patch("apps.certs.services.onboarding_repository.connection")
    def test_repository_marks_batch_committed_with_actor(self, connection) -> None:
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.description = [
            ("batch_id",),
            ("vessel_id",),
            ("onboarding_session_id",),
            ("pdf_blob_ids_json",),
            ("pdf_count",),
            ("status",),
            ("created_at",),
            ("created_by",),
            ("ocr_completed_at",),
            ("review_started_at",),
            ("committed_at",),
            ("committed_by",),
            ("cancelled_at",),
            ("cancelled_by",),
            ("validation_blocks_json",),
            ("validation_warns_json",),
            ("report_csv_blob_id",),
        ]
        cursor.fetchall.return_value = [(
            "batch-1",
            "vessel-1",
            "session-1",
            '["blob-1"]',
            1,
            "committed",
            "2026-06-26T09:00:00Z",
            "dpa-1",
            "2026-06-26T09:05:00Z",
            "2026-06-26T09:10:00Z",
            "2026-06-26T09:15:00Z",
            "dpa-1",
            None,
            None,
            "[]",
            "[]",
            None,
        )]

        repository = OnboardingRepository()
        batch = repository.mark_batch_committed("batch-1", actor={"id": "dpa-1"})

        self.assertEqual(batch["status"], "committed")
        self.assertEqual(batch["committed_by"], "dpa-1")
        self.assertIn("committed_at", cursor.execute.call_args_list[0].args[0])


if __name__ == "__main__":
    unittest.main()
