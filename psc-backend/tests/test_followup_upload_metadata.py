import unittest
import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.inspection.followup_views import (
    REPORT_FILE_NAME_MAX_LENGTH,
    _truncate_file_name,
    _truncate_text,
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
