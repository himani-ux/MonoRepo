from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import timedelta

from django.db import connection, transaction
from django.utils import timezone

from apps.safety.models import (
    CorrectiveAction,
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
from apps.safety.services.archive_state import archive_filter

from .orphan_attachment_cleanup import OrphanAttachmentCleanupService


DEFAULT_RETENTION_DAYS = 1095
DEFAULT_RETENTION_CRON = "0 2 * * *"
SYSTEM_RETENTION_PARENT_TABLE = "system_retention_job"


@dataclass(frozen=True)
class RetentionDeletedRecord:
    record_table: str
    record_id: int
    reference: str
    deleted_attachment_count: int
    deleted_history_count: int


@dataclass(frozen=True)
class RetentionJobResult:
    retention_days: int
    deleted_record_count: int
    deleted_attachment_count: int
    deleted_records: list[RetentionDeletedRecord]


class SafetyRetentionJob:
    def __init__(
        self,
        *,
        incident_model=Incident,
        incident_phase_log_model=IncidentPhaseLog,
        scm_model=SCMMeeting,
        scm_agenda_model=SCMAgendaItem,
        scm_attendance_model=SCMAttendance,
        soi_model=SOIInspection,
        soi_finding_model=SOIFinding,
        soi_area_model=SOIInspectionArea,
        soi_trainee_model=SOITrainee,
        corrective_action_model=CorrectiveAction,
        field_history_model=SafetyFieldHistory,
        attachment_cleanup_service: OrphanAttachmentCleanupService | None = None,
    ) -> None:
        self.incident_model = incident_model
        self.incident_phase_log_model = incident_phase_log_model
        self.scm_model = scm_model
        self.scm_agenda_model = scm_agenda_model
        self.scm_attendance_model = scm_attendance_model
        self.soi_model = soi_model
        self.soi_finding_model = soi_finding_model
        self.soi_area_model = soi_area_model
        self.soi_trainee_model = soi_trainee_model
        self.corrective_action_model = corrective_action_model
        self.field_history_model = field_history_model
        self.attachment_cleanup_service = attachment_cleanup_service or OrphanAttachmentCleanupService(
            incident_model=incident_model,
            scm_model=scm_model,
            soi_model=soi_model,
            soi_finding_model=soi_finding_model,
            field_history_model=field_history_model,
        )

    def run(self, *, now=None, retention_days: int | None = None) -> RetentionJobResult:
        resolved_now = now or timezone.now()
        resolved_retention_days = retention_days if retention_days is not None else get_retention_days()
        cutoff = resolved_now - timedelta(days=resolved_retention_days)
        deleted_records: list[RetentionDeletedRecord] = []
        deleted_attachment_count = 0

        for record in self._iter_candidates(cutoff=cutoff):
            deleted_record = self._purge_record(
                record=record,
                now=resolved_now,
                cutoff=cutoff,
                retention_days=resolved_retention_days,
            )
            deleted_records.append(deleted_record)
            deleted_attachment_count += deleted_record.deleted_attachment_count

        return RetentionJobResult(
            retention_days=resolved_retention_days,
            deleted_record_count=len(deleted_records),
            deleted_attachment_count=deleted_attachment_count,
            deleted_records=deleted_records,
        )

    def _iter_candidates(self, *, cutoff):
        table_names = self._table_names()

        if self.incident_model._meta.db_table in table_names:
            incidents = (
                self.incident_model.objects.filter(is_deleted=False)
                .filter(archive_filter(archived=True))
                .filter(archived_at__lte=cutoff)
                .order_by("archived_at", "id")
            )
            for row in incidents:
                yield row

        if self.scm_model._meta.db_table in table_names:
            meetings = (
                self.scm_model.objects.filter(is_deleted=False)
                .filter(archive_filter(archived=True))
                .filter(archived_at__lte=cutoff)
                .order_by("archived_at", "id")
            )
            for row in meetings:
                yield row

        if self.soi_model._meta.db_table in table_names:
            inspections = (
                self.soi_model.objects.filter(is_deleted=False)
                .filter(archive_filter(archived=True))
                .filter(archived_at__lte=cutoff)
                .order_by("archived_at", "id")
            )
            for row in inspections:
                yield row

    def _purge_record(self, *, record, now, cutoff, retention_days: int) -> RetentionDeletedRecord:
        record_table = record._meta.db_table
        record_id = int(record.pk)
        reference = self._record_reference(record)
        attachment_paths = self.attachment_cleanup_service.collect_paths_for_parent(
            parent_table=record_table,
            parent_id=record_id,
        )

        with transaction.atomic():
            attachment_result = self.attachment_cleanup_service.delete_paths(
                attachment_paths,
                now=now,
                reason=f"Attachment file removed during Step 7.8 retention purge after {retention_days} days in soft archive.",
                audit_parent_table=SYSTEM_RETENTION_PARENT_TABLE,
                audit_parent_id=record_id,
                field_name="retention_attachment_purge",
            )
            deleted_history_count = self._delete_record_family(record)
            self._record_retention_summary(
                record_table=record_table,
                record_id=record_id,
                reference=reference,
                archived_at=getattr(record, "archived_at", None),
                cutoff=cutoff,
                now=now,
                deleted_attachment_count=len(attachment_result.deleted_paths),
                missing_attachment_paths=attachment_result.missing_paths,
            )

        return RetentionDeletedRecord(
            record_table=record_table,
            record_id=record_id,
            reference=reference,
            deleted_attachment_count=len(attachment_result.deleted_paths),
            deleted_history_count=deleted_history_count,
        )

    def _delete_record_family(self, record) -> int:
        if isinstance(record, self.incident_model):
            return self._delete_incident_family(record)
        if isinstance(record, self.scm_model):
            return self._delete_scm_family(record)
        if isinstance(record, self.soi_model):
            return self._delete_soi_family(record)
        record.delete()
        return 0

    def _delete_incident_family(self, incident) -> int:
        deleted_history_count = self._delete_parent_history(incident._meta.db_table, int(incident.pk))
        if self.incident_phase_log_model._meta.db_table in self._table_names():
            self.incident_phase_log_model.objects.filter(incident_id=incident.pk).delete()
        if self.corrective_action_model._meta.db_table in self._table_names():
            self.corrective_action_model.objects.filter(source_table=incident._meta.db_table, source_id=incident.pk).delete()
        incident.delete()
        return deleted_history_count

    def _delete_scm_family(self, meeting) -> int:
        deleted_history_count = self._delete_parent_history(meeting._meta.db_table, int(meeting.pk))
        if self.scm_agenda_model._meta.db_table in self._table_names():
            self.scm_agenda_model.objects.filter(meeting_id=meeting.pk).delete()
        if self.scm_attendance_model._meta.db_table in self._table_names():
            self.scm_attendance_model.objects.filter(meeting_id=meeting.pk).delete()
        if self.corrective_action_model._meta.db_table in self._table_names():
            self.corrective_action_model.objects.filter(source_table=meeting._meta.db_table, source_id=meeting.pk).delete()
        meeting.delete()
        return deleted_history_count

    def _delete_soi_family(self, inspection) -> int:
        deleted_history_count = self._delete_parent_history(inspection._meta.db_table, int(inspection.pk))
        finding_ids: list[int] = []
        if self.soi_finding_model._meta.db_table in self._table_names():
            finding_ids = list(self.soi_finding_model.objects.filter(inspection_id=inspection.pk).values_list("id", flat=True))
            for finding_id in finding_ids:
                deleted_history_count += self._delete_parent_history(self.soi_finding_model._meta.db_table, int(finding_id))
            self.soi_finding_model.objects.filter(inspection_id=inspection.pk).delete()
        if finding_ids and self.corrective_action_model._meta.db_table in self._table_names():
            self.corrective_action_model.objects.filter(
                source_table=self.soi_finding_model._meta.db_table,
                source_id__in=finding_ids,
            ).delete()
        if self.soi_area_model._meta.db_table in self._table_names():
            self.soi_area_model.objects.filter(inspection_id=inspection.pk).delete()
        if self.soi_trainee_model._meta.db_table in self._table_names():
            self.soi_trainee_model.objects.filter(inspection_id=inspection.pk).delete()
        if self.corrective_action_model._meta.db_table in self._table_names():
            self.corrective_action_model.objects.filter(source_table=inspection._meta.db_table, source_id=inspection.pk).delete()
        inspection.delete()
        return deleted_history_count

    def _delete_parent_history(self, parent_table: str, parent_id: int) -> int:
        if self.field_history_model._meta.db_table not in self._table_names():
            return 0
        queryset = self.field_history_model.objects.filter(parent_table=parent_table, parent_id=parent_id)
        deleted_count, _ = queryset.delete()
        return int(deleted_count)

    def _record_retention_summary(
        self,
        *,
        record_table: str,
        record_id: int,
        reference: str,
        archived_at,
        cutoff,
        now,
        deleted_attachment_count: int,
        missing_attachment_paths: list[str],
    ) -> None:
        if self.field_history_model._meta.db_table not in self._table_names():
            return

        old_value = {
            "record_table": record_table,
            "record_id": record_id,
            "reference": reference,
            "archived_at": archived_at.isoformat() if archived_at is not None else None,
            "retention_cutoff": cutoff.isoformat(),
        }
        new_value = {
            "deleted_at": now.isoformat(),
            "deleted_attachment_count": deleted_attachment_count,
            "missing_attachment_paths": list(missing_attachment_paths),
            "status": "hard_deleted",
        }
        self.field_history_model.objects.create(
            parent_table=SYSTEM_RETENTION_PARENT_TABLE,
            parent_id=record_id,
            field_name="retention_hard_delete",
            old_value=old_value,
            new_value=new_value,
            change_reason="Safety record hard-deleted by the daily Step 7.8 retention job.",
            actor_user_id="system",
            actor_role_code="SYSTEM",
            schema_version=1,
        )

    def _record_reference(self, record) -> str:
        if hasattr(record, "incident_number"):
            return str(record.incident_number)
        if hasattr(record, "scm_number"):
            return str(record.scm_number)
        if hasattr(record, "inspection_reference"):
            return str(record.inspection_reference)
        return str(record.pk)

    @staticmethod
    def _table_names() -> set[str]:
        return set(connection.introspection.table_names())


def get_retention_days() -> int:
    raw_value = os.environ.get("SAFETY_RETENTION_DAYS")
    if raw_value in (None, ""):
        return DEFAULT_RETENTION_DAYS
    try:
        parsed = int(raw_value)
    except ValueError:
        return DEFAULT_RETENTION_DAYS
    return parsed if parsed > 0 else DEFAULT_RETENTION_DAYS


def get_retention_cron() -> str:
    return os.environ.get("SAFETY_RETENTION_CRON", DEFAULT_RETENTION_CRON)


def run_retention_job(*, now=None, retention_days: int | None = None) -> RetentionJobResult:
    return SafetyRetentionJob().run(now=now, retention_days=retention_days)
