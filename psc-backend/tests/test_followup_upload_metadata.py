import unittest
import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict

from apps.inspection.followup_views import (
    MAX_FOLLOW_UP_REPORT_SIZE,
    REPORT_FILE_NAME_MAX_LENGTH,
    _get_report_files,
    _truncate_file_name,
    _truncate_text,
    _validate_report_files,
)


class FollowUpUploadMetadataTests(unittest.TestCase):
    def test_truncate_file_name_preserves_extension_within_db_limit(self):
        long_name = f"{'a' * 300}.pdf"

        result = _truncate_file_name(long_name)

        self.assertLessEqual(len(result), REPORT_FILE_NAME_MAX_LENGTH)
        self.assertTrue(result.endswith(".pdf"))

    def test_truncate_text_handles_empty_values(self):
        self.assertEqual(_truncate_text(None, 10), "")
        self.assertEqual(_truncate_text("  abcdef  ", 3), "abc")

    def test_validate_report_files_allows_three_pdfs(self):
        files = [
            SimpleUploadedFile("one.pdf", b"%PDF-1.4", content_type="application/pdf"),
            SimpleUploadedFile("two.pdf", b"%PDF-1.4", content_type="application/pdf"),
            SimpleUploadedFile("three.pdf", b"%PDF-1.4", content_type="application/pdf"),
        ]

        self.assertEqual(_validate_report_files(files), "")

    def test_validate_report_files_rejects_four_pdfs(self):
        files = [
            SimpleUploadedFile("one.pdf", b"%PDF-1.4", content_type="application/pdf"),
            SimpleUploadedFile("two.pdf", b"%PDF-1.4", content_type="application/pdf"),
            SimpleUploadedFile("three.pdf", b"%PDF-1.4", content_type="application/pdf"),
            SimpleUploadedFile("four.pdf", b"%PDF-1.4", content_type="application/pdf"),
        ]

        self.assertEqual(
            _validate_report_files(files),
            "Up to 3 follow-up report PDFs can be attached.",
        )

    def test_validate_report_files_rejects_non_pdf(self):
        files = [
            SimpleUploadedFile("image.png", b"png", content_type="image/png"),
        ]

        self.assertEqual(
            _validate_report_files(files),
            "Each follow-up report must be a PDF file.",
        )

    def test_validate_report_files_rejects_pdf_over_5mb(self):
        files = [
            SimpleUploadedFile(
                "large.pdf",
                b"0" * (MAX_FOLLOW_UP_REPORT_SIZE + 1),
                content_type="application/pdf",
            ),
        ]

        self.assertEqual(
            _validate_report_files(files),
            "Each follow-up report file must be 5MB or smaller.",
        )

    def test_get_report_files_collects_repeated_and_legacy_fields(self):
        first = SimpleUploadedFile("one.pdf", b"%PDF-1.4", content_type="application/pdf")
        second = SimpleUploadedFile("two.pdf", b"%PDF-1.4", content_type="application/pdf")
        legacy = SimpleUploadedFile("legacy.pdf", b"%PDF-1.4", content_type="application/pdf")
        request = type("Request", (), {})()
        request.FILES = MultiValueDict({
            "report_files": [first, second],
            "report_file": [legacy],
        })

        self.assertEqual(_get_report_files(request), [first, second, legacy])
