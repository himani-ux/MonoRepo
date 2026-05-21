from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path
import shutil
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_soi_tables


bootstrap_django()

from apps.safety.models import EvidenceItem, Incident, SafetyFieldHistory, SOIFinding, SOIInspection
from apps.safety.services.field_history_recorder import parse_history_value
from apps.safety.tasks.orphan_attachment_cleanup import cleanup_orphan_attachments


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class OrphanAttachmentCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_soi_tables()
        self.current_at = aware(2026, 4, 30, 13, 0)
        self.storage_root = Path("test-output") / "orphan-cleanup"
        shutil.rmtree(self.storage_root, ignore_errors=True)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.original_export_root = os.environ.get("SAFETY_EXPORT_ROOT")
        os.environ["SAFETY_EXPORT_ROOT"] = str(self.storage_root)

        self.kept_incident_path = self._write_fixture("7/incidents/INC-KEEP/bridge-photo.jpg")
        self.kept_soi_path = self._write_fixture("7/soi/SOI-KEEP/engine-photo.jpg")
        self.orphan_path = self._write_fixture("7/incidents/INC-ORPHAN/lost-photo.jpg")
        self.export_artifact = self._write_fixture("7/exports/safety-dashboard.pdf")

        incident = Incident.objects.create(
            incident_number="INC/2026/KEEP",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=3,
            occurred_at=self.current_at,
            reported_at=self.current_at,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        EvidenceItem.objects.create(
            incident=incident,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Kept incident attachment",
            metadata_json={"attachment_path": self.kept_incident_path},
            created_by="master-7",
            schema_version=1,
        )

        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/2026/KEEP",
            cycle_label="Q2/2026",
            state=SOIInspection.State.REPORTED,
            planned_date=self.current_at.date(),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            checklist_unique_id="SOI-KEEP-1",
            checklist_generated_at=self.current_at,
            checklist_format=SOIInspection.ChecklistFormat.PDF,
            fieldwork_started_at=self.current_at,
            reported_at=self.current_at,
            created_by="co-7",
            updated_by="co-7",
            schema_version=1,
        )
        SOIFinding.objects.create(
            inspection_id=inspection.pk,
            area_id=8,
            item_id=8001,
            title="Kept SOI finding",
            description="Photo should remain because parent record still exists.",
            severity="HIGH",
            priority="HIGH",
            status=SOIFinding.Status.OPEN,
            photo_attachment_path=self.kept_soi_path,
            created_by="co-7",
            schema_version=1,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.storage_root, ignore_errors=True)
        if self.original_export_root is None:
            os.environ.pop("SAFETY_EXPORT_ROOT", None)
        else:
            os.environ["SAFETY_EXPORT_ROOT"] = self.original_export_root

    def test_cleanup_deletes_unreferenced_attachment_and_skips_export_artifacts(self) -> None:
        result = cleanup_orphan_attachments(now=self.current_at)

        self.assertEqual(result.deleted_paths, [str(Path(self.orphan_path).resolve())])
        self.assertFalse(Path(self.orphan_path).exists())
        self.assertTrue(Path(self.kept_incident_path).exists())
        self.assertTrue(Path(self.kept_soi_path).exists())
        self.assertTrue(Path(self.export_artifact).exists())

        audit_row = SafetyFieldHistory.objects.get(
            parent_table="system_attachment_store",
            field_name="orphan_attachment_cleanup",
        )
        payload = parse_history_value(audit_row.old_value)
        self.assertEqual(payload["absolute_path"], str(Path(self.orphan_path).resolve()))
        self.assertIsNone(audit_row.new_value)

    def _write_fixture(self, relative_path: str) -> str:
        path = self.storage_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
        return str(path.resolve())
