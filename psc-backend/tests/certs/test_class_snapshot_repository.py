from __future__ import annotations

import os
import unittest
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.exceptions import SuspiciousFileOperation
from django.test import override_settings

from apps.certs.services.snapshot_repository import ClassSnapshotRepository


HANDOVER_ROOT = Path(__file__).resolve().parents[4]
REFERENCE_PACK = HANDOVER_ROOT / "reference-packs" / "Class-Reference-Reports"


class FakeBlobRepository:
    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path

    def get_blob(self, blob_id: str):
        return {"blob_id": blob_id, "blob_storage_path": self.storage_path}


class CertClassSnapshotRepositoryTests(unittest.TestCase):
    @override_settings(UPLOAD_BASE_PATH=HANDOVER_ROOT)
    def test_parse_snapshot_pdf_loads_blob_path_and_invokes_class_parser(self) -> None:
        pdf_path = REFERENCE_PACK / "Class Status Report East Ayutthaya 6th May 2026.pdf"
        repository = ClassSnapshotRepository(
            pdf_blobs=FakeBlobRepository(str(pdf_path.relative_to(HANDOVER_ROOT))),
            reconciliation=None,
        )

        parsed = repository._parse_snapshot_pdf({"pdf_blob_id": "blob-1", "class_society": "KR"})

        self.assertEqual(parsed.parse_status, "success")
        self.assertEqual(parsed.parser_version, "kr-pdfplumber-v1")
        self.assertEqual(parsed.payload["source"], "pdfplumber_text")
        self.assertEqual(parsed.payload["vessel"]["imo"], "9584293")
        self.assertGreaterEqual(len(parsed.payload["rows"]), 40)

    @override_settings(UPLOAD_BASE_PATH=HANDOVER_ROOT)
    def test_parse_snapshot_pdf_rejects_blob_path_outside_upload_base(self) -> None:
        repository = ClassSnapshotRepository(
            pdf_blobs=FakeBlobRepository("../outside-class-status.pdf"),
            reconciliation=None,
        )

        with self.assertRaises(SuspiciousFileOperation):
            repository._parse_snapshot_pdf({"pdf_blob_id": "blob-1", "class_society": "KR"})


if __name__ == "__main__":
    unittest.main()
