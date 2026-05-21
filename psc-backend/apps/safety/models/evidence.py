from __future__ import annotations

from datetime import timedelta

from django.db import models

from .base import PublicIdMixin
from .incident import Incident


class IncidentEvidence(PublicIdMixin):
    class TabCode(models.TextChoices):
        POSITION = "POSITION", "Position"
        PEOPLE = "PEOPLE", "People"
        PARTS = "PARTS", "Parts"
        PAPER = "PAPER", "Paper"
        ELECTRONIC = "ELECTRONIC", "Electronic"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="evidence_tabs")
    tab_code = models.CharField(max_length=16, choices=TabCode.choices)
    summary = models.TextField(blank=True, default="")
    entry_count = models.PositiveIntegerField(default=0)
    structured_data = models.JSONField(default=dict, blank=True)
    status_chip = models.CharField(max_length=64, blank=True, default="")
    na_justification = models.TextField(blank=True, null=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_incident_evidence"
        constraints = [
            models.UniqueConstraint(fields=("incident", "tab_code"), name="uq_vims_safety_incident_evidence_tab")
        ]
        indexes = [
            models.Index(fields=("incident", "tab_code"), name="ix_safe_inc_ev_tab"),
        ]


class EvidenceItem(PublicIdMixin):
    class ItemType(models.TextChoices):
        MATRIX = "MATRIX", "Evidence Matrix"
        PHYSICAL = "PHYSICAL", "Physical Evidence"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="evidence_items")
    evidence_tab = models.ForeignKey(
        IncidentEvidence,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="items",
    )
    item_type = models.CharField(max_length=16, choices=ItemType.choices)
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True, default="")
    source_label = models.CharField(max_length=128, blank=True, default="")
    finding = models.CharField(max_length=256, blank=True, default="")
    pro_evidence = models.TextField(blank=True, default="")
    con_evidence = models.TextField(blank=True, default="")
    comments = models.TextField(blank=True, default="")
    metadata_json = models.JSONField(default=dict, blank=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_evidence_item"
        indexes = [
            models.Index(fields=("incident", "item_type"), name="ix_safe_evi_kind"),
        ]


class ChainOfCustody(PublicIdMixin):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="chain_of_custody_rows")
    evidence_item = models.ForeignKey(
        EvidenceItem,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="custody_rows",
    )
    description = models.TextField()
    collection_timestamp = models.DateTimeField()
    collector_name = models.CharField(max_length=128)
    collector_signature = models.TextField()
    storage_location = models.CharField(max_length=256)
    witness_signature = models.TextField()
    current_holder = models.CharField(max_length=128)
    handover_log = models.JSONField(default=list, blank=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_chain_of_custody"
        indexes = [
            models.Index(fields=("incident", "collection_timestamp"), name="ix_vims_safety_coc_incident"),
        ]


class WitnessInterview(PublicIdMixin):
    class InterviewType(models.TextChoices):
        FORMAL = "FORMAL", "Formal"
        INFORMAL = "INFORMAL", "Informal"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="witness_interviews")
    witness_name = models.CharField(max_length=128)
    interview_type = models.CharField(max_length=16, choices=InterviewType.choices)
    reason_formal_impossible = models.TextField(blank=True, null=True)
    make_acquaintance_notes = models.TextField(blank=True, default="")
    introduction_notes = models.TextField(blank=True, default="")
    meeting_notes = models.TextField(blank=True, default="")
    conclusion_notes = models.TextField(blank=True, default="")
    question_rows = models.JSONField(default=list, blank=True)
    read_back_confirmed = models.BooleanField(default=False)
    witness_signature = models.TextField(blank=True, null=True)
    copy_to_witness_recorded = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    phase_count = models.PositiveSmallIntegerField(default=0)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_witness_interview"
        indexes = [
            models.Index(fields=("incident", "interview_type"), name="ix_vims_safety_interview_type"),
        ]


class EvidenceDeadlineTask(PublicIdMixin):
    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        ALERT = "ALERT", "Alert"
        HARD_ALARM = "HARD_ALARM", "Hard Alarm"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        OVERDUE = "OVERDUE", "Overdue"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="evidence_deadline_tasks")
    task_code = models.CharField(max_length=32)
    title = models.CharField(max_length=128)
    due_at = models.DateTimeField()
    due_within = models.DurationField(default=timedelta)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.INFO)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    completed_at = models.DateTimeField(blank=True, null=True)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    justification = models.TextField(blank=True, null=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "vims_safety_evidence_deadline_task"
        constraints = [
            models.UniqueConstraint(fields=("incident", "task_code"), name="uq_vims_safety_deadline_task_code")
        ]
        indexes = [
            models.Index(fields=("incident", "due_at"), name="ix_vims_safety_deadline_due"),
        ]
