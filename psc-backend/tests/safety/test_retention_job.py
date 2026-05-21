from __future__ import annotations
import os
from datetime import date, datetime, timedelta
from pathlib import Path
import shutil
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_scm_tables, recreate_soi_tables


bootstrap_django()

from apps.safety.models import (
    CorrectiveAction,
    EvidenceItem,
    Incident,
    IncidentPhaseLog,
    SCMAgendaItem,
    SCMAttendance,
    SCMMeeting,
    SafetyFieldHistory,
    SOIFinding,
    SOIInspection,
    SOIInspectionArea,
    SOITrainee,
)
from apps.safety.services.field_history_recorder import parse_history_value
from apps.safety.tasks.retention_job import SYSTEM_RETENTION_PARENT_TABLE, run_retention_job


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class RetentionJobTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        recreate_soi_tables()
        self.current_at = aware(2026, 4, 30, 12, 0)
        self.storage_root = Path("test-output") / "retention-job"
        shutil.rmtree(self.storage_root, ignore_errors=True)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.original_export_root = os.environ.get("SAFETY_EXPORT_ROOT")
        os.environ["SAFETY_EXPORT_ROOT"] = str(self.storage_root)

        self.incident_path = self._write_attachment("7/incidents/INC-OLD/bridge-photo.jpg")
        self.scm_path = self._write_attachment("7/scm/SCM-OLD/master-signature.jpg")
        self.soi_path = self._write_attachment("7/soi/SOI-OLD/engine-photo.jpg")
        self.active_path = self._write_attachment("7/incidents/INC-ACTIVE/keep.jpg")

        self._seed_archived_incident()
        self._seed_archived_scm()
        self._seed_archived_soi()
        self._seed_active_incident()

    def tearDown(self) -> None:
        shutil.rmtree(self.storage_root, ignore_errors=True)
        if self.original_export_root is None:
            os.environ.pop("SAFETY_EXPORT_ROOT", None)
        else:
            os.environ["SAFETY_EXPORT_ROOT"] = self.original_export_root

    def test_retention_job_hard_deletes_archived_records_and_logs_system_summary(self) -> None:
        result = run_retention_job(now=self.current_at)

        self.assertEqual(result.retention_days, 1095)
        self.assertEqual(result.deleted_record_count, 3)
        self.assertEqual(result.deleted_attachment_count, 3)

        self.assertFalse(Incident.objects.filter(pk=self.archived_incident.pk).exists())
        self.assertFalse(SCMMeeting.objects.filter(pk=self.archived_meeting.pk).exists())
        self.assertFalse(SOIInspection.objects.filter(pk=self.archived_inspection.pk).exists())
        self.assertTrue(Incident.objects.filter(pk=self.active_incident.pk).exists())

        self.assertFalse(Path(self.incident_path).exists())
        self.assertFalse(Path(self.scm_path).exists())
        self.assertFalse(Path(self.soi_path).exists())
        self.assertTrue(Path(self.active_path).exists())

        self.assertFalse(IncidentPhaseLog.objects.filter(incident_id=self.archived_incident.pk).exists())
        self.assertFalse(CorrectiveAction.objects.filter(source_table=Incident._meta.db_table, source_id=self.archived_incident.pk).exists())
        self.assertFalse(SCMAgendaItem.objects.filter(meeting_id=self.archived_meeting.pk).exists())
        self.assertFalse(SCMAttendance.objects.filter(meeting_id=self.archived_meeting.pk).exists())
        self.assertFalse(SOIInspectionArea.objects.filter(inspection_id=self.archived_inspection.pk).exists())
        self.assertFalse(SOITrainee.objects.filter(inspection_id=self.archived_inspection.pk).exists())
        self.assertFalse(SOIFinding.objects.filter(inspection_id=self.archived_inspection.pk).exists())

        self.assertFalse(
            SafetyFieldHistory.objects.filter(
                parent_table=Incident._meta.db_table,
                parent_id=self.archived_incident.pk,
            ).exists()
        )
        self.assertFalse(
            SafetyFieldHistory.objects.filter(
                parent_table=SCMMeeting._meta.db_table,
                parent_id=self.archived_meeting.pk,
            ).exists()
        )
        self.assertFalse(
            SafetyFieldHistory.objects.filter(
                parent_table=SOIInspection._meta.db_table,
                parent_id=self.archived_inspection.pk,
            ).exists()
        )

        summary_rows = SafetyFieldHistory.objects.filter(
            parent_table=SYSTEM_RETENTION_PARENT_TABLE,
            field_name="retention_hard_delete",
        ).order_by("id")
        self.assertEqual(summary_rows.count(), 3)
        references = {parse_history_value(row.old_value)["reference"] for row in summary_rows}
        self.assertEqual(references, {"INC/2022/001", "SCM/2022/001", "SOI/2022/001"})

        attachment_rows = SafetyFieldHistory.objects.filter(
            parent_table=SYSTEM_RETENTION_PARENT_TABLE,
            field_name="retention_attachment_purge",
        )
        self.assertEqual(attachment_rows.count(), 3)

    def _seed_archived_incident(self) -> None:
        archived_at = self.current_at - timedelta(days=1096)
        self.archived_incident = Incident.objects.create(
            incident_number="INC/2022/001",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            current_phase=9,
            occurred_at=archived_at,
            reported_at=archived_at,
            is_archived=True,
            archived_at=archived_at,
            narrative="Archived incident ready for retention purge.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        EvidenceItem.objects.create(
            incident=self.archived_incident,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Bridge photo",
            metadata_json={"attachment_path": self.incident_path},
            created_by="dpa-1",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=self.archived_incident,
            phase_from=8,
            phase_to=9,
            transition_type=IncidentPhaseLog.TransitionType.CLOSE,
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )
        CorrectiveAction.objects.create(
            source_table=Incident._meta.db_table,
            source_id=self.archived_incident.pk,
            title="Archived incident corrective action",
            description="Should purge with parent incident.",
            status=CorrectiveAction.Status.CLOSED,
            created_by="dpa-1",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=Incident._meta.db_table,
            parent_id=self.archived_incident.pk,
            field_name="attachment_path",
            old_value=None,
            new_value={"attachment_path": self.incident_path},
            change_reason="Fixture field-history attachment reference.",
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )

    def _seed_archived_scm(self) -> None:
        archived_at = self.current_at - timedelta(days=1097)
        self.archived_meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="SCM/2022/001",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2022, 4, 20),
            meeting_time_local="09:00:00",
            location="At Sea",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=archived_at,
            master_signed_off_by="master-7",
            is_archived=True,
            archived_at=archived_at,
            created_by="co-7",
            updated_by="master-7",
            schema_version=1,
        )
        SCMAgendaItem.objects.create(
            meeting_id=self.archived_meeting.pk,
            agenda_item_number=1,
            section_label="Findings",
            auto_populated=False,
            content="Closed items archived with parent meeting.",
            schema_version=1,
        )
        SCMAttendance.objects.create(
            meeting_id=self.archived_meeting.pk,
            crew_id="crew-1",
            rank_name="Chief Officer",
            display_name="Chief Officer One",
            present=True,
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=SCMMeeting._meta.db_table,
            parent_id=self.archived_meeting.pk,
            field_name="signature_attachment",
            old_value=None,
            new_value={"attachment_path": self.scm_path},
            change_reason="Fixture SCM attachment reference.",
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )

    def _seed_archived_soi(self) -> None:
        archived_at = self.current_at - timedelta(days=1098)
        self.archived_inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/2022/001",
            cycle_label="Q2/2022",
            state=SOIInspection.State.CLOSED,
            planned_date=date(2022, 4, 18),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            checklist_unique_id="SOI-UID-2022-001",
            checklist_generated_at=archived_at,
            checklist_format=SOIInspection.ChecklistFormat.PDF,
            fieldwork_started_at=archived_at,
            reported_at=archived_at,
            closed_at=archived_at,
            is_archived=True,
            archived_at=archived_at,
            created_by="co-7",
            updated_by="master-7",
            schema_version=1,
        )
        SOIInspectionArea.objects.create(
            inspection_id=self.archived_inspection.pk,
            area_id=8,
            inspected=True,
            last_inspected_at=archived_at,
            schema_version=1,
        )
        SOITrainee.objects.create(
            inspection_id=self.archived_inspection.pk,
            crew_id="cadet-1",
            trainee_slot=1,
            schema_version=1,
        )
        finding = SOIFinding.objects.create(
            inspection_id=self.archived_inspection.pk,
            area_id=8,
            item_id=8001,
            title="Archived SOI finding",
            description="Engine marker no longer visible.",
            severity="HIGH",
            priority="HIGH",
            status=SOIFinding.Status.CLOSED,
            photo_attachment_path=self.soi_path,
            created_by="co-7",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=SOIFinding._meta.db_table,
            parent_id=finding.pk,
            field_name="photo_attachment_path",
            old_value=None,
            new_value={"photo_attachment_path": self.soi_path},
            change_reason="Fixture SOI attachment reference.",
            actor_user_id="co-7",
            actor_role_code="CO",
            schema_version=1,
        )

    def _seed_active_incident(self) -> None:
        self.active_incident = Incident.objects.create(
            incident_number="INC/2026/ACTIVE",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=4,
            occurred_at=self.current_at,
            reported_at=self.current_at,
            narrative="Active incident must survive retention job.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        EvidenceItem.objects.create(
            incident=self.active_incident,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Active evidence",
            metadata_json={"attachment_path": self.active_path},
            created_by="master-7",
            schema_version=1,
        )

    def _write_attachment(self, relative_path: str) -> str:
        path = self.storage_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
        return str(path.resolve())
