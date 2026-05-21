from __future__ import annotations
import os
from pathlib import Path
import shutil
import unittest
from types import SimpleNamespace

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.services.attachment_replace_handler import AttachmentReplaceHandler
from apps.safety.services.field_history_recorder import parse_history_value


class SameFilenameReplaceTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        self.storage_root = Path("test-output") / "same-filename-replace"
        shutil.rmtree(self.storage_root, ignore_errors=True)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.original_export_root = os.environ.get("SAFETY_EXPORT_ROOT")
        os.environ["SAFETY_EXPORT_ROOT"] = str(self.storage_root)

        self.incident = Incident.objects.create(
            incident_number="INC/2026/REPLACE",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        self.relative_path = "7/incidents/INC-2026-REPLACE/bridge-photo.jpg"
        self.target_path = self.storage_root / self.relative_path
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        self.target_path.write_bytes(b"old-bytes")
        self.handler = AttachmentReplaceHandler(storage_root=self.storage_root)
        self.user = SimpleNamespace(id="master-7", username="master-7", role_name="MASTER")

    def tearDown(self) -> None:
        shutil.rmtree(self.storage_root, ignore_errors=True)
        if self.original_export_root is None:
            os.environ.pop("SAFETY_EXPORT_ROOT", None)
        else:
            os.environ["SAFETY_EXPORT_ROOT"] = self.original_export_root

    def test_replace_in_place_overwrites_existing_file_and_captures_audit_metadata(self) -> None:
        result = self.handler.replace_in_place(
            relative_path=self.relative_path,
            content=b"new-longer-bytes",
            user=self.user,
            parent_table=Incident._meta.db_table,
            parent_id=self.incident.pk,
        )

        self.assertTrue(result.replaced)
        self.assertEqual(result.relative_path, self.relative_path)
        self.assertEqual(self.target_path.read_bytes(), b"new-longer-bytes")

        audit_row = SafetyFieldHistory.objects.get(pk=result.audit_row_id)
        old_value = parse_history_value(audit_row.old_value)
        new_value = parse_history_value(audit_row.new_value)
        self.assertEqual(old_value["relative_path"], self.relative_path)
        self.assertEqual(new_value["relative_path"], self.relative_path)
        self.assertEqual(old_value["file_name"], "bridge-photo.jpg")
        self.assertEqual(new_value["file_name"], "bridge-photo.jpg")
        self.assertLess(old_value["byte_size"], new_value["byte_size"])
        self.assertTrue(new_value["replace_in_place"])
