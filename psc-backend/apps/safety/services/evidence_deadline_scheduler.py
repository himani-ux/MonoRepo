from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from apps.safety.models import EvidenceDeadlineTask, Incident


@dataclass(frozen=True)
class DeadlineTemplate:
    code: str
    due_within: timedelta
    title: str


DEFAULT_DEADLINE_TEMPLATES = (
    DeadlineTemplate("VDR_CAPTURE", timedelta(hours=12), "Capture VDR data"),
    DeadlineTemplate("ECDIS_SNAPSHOT", timedelta(hours=24), "Capture ECDIS track snapshot"),
    DeadlineTemplate("AIS_REQUEST", timedelta(hours=24), "Request AIS shore-side record"),
    DeadlineTemplate("PHOTO_WALKAROUND", timedelta(hours=48), "Complete 4-angle photo walk-around"),
    DeadlineTemplate("FORMAL_STATEMENTS", timedelta(days=7), "Collect formal witness statements"),
)


class EvidenceDeadlineScheduler:
    task_model = EvidenceDeadlineTask

    def schedule_default_tasks(self, incident: Incident, *, created_by: str) -> list[EvidenceDeadlineTask]:
        base_at = incident.occurred_at or incident.reported_at or timezone.now()
        tasks: list[EvidenceDeadlineTask] = []
        for template in DEFAULT_DEADLINE_TEMPLATES:
            task, _ = self.task_model.objects.get_or_create(
                incident=incident,
                task_code=template.code,
                defaults={
                    "title": template.title,
                    "due_at": base_at + template.due_within,
                    "due_within": template.due_within,
                    "severity": self._resolve_severity(incident, template.code),
                    "status": EvidenceDeadlineTask.Status.PENDING,
                    "schema_version": incident.schema_version or 1,
                    "created_by": created_by,
                    "updated_by": created_by,
                },
            )
            tasks.append(task)
        return tasks

    def _resolve_severity(self, incident: Incident, task_code: str) -> str:
        if task_code == "VDR_CAPTURE" and incident.risk_band == Incident.RiskBand.RED:
            return EvidenceDeadlineTask.Severity.HARD_ALARM
        return EvidenceDeadlineTask.Severity.ALERT
