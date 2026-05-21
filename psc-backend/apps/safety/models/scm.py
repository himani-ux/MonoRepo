from __future__ import annotations

from django.db import models
from django.db.models import Q

from .base import PublicIdMixin


class SCMMeeting(PublicIdMixin):
    class MeetingType(models.TextChoices):
        REGULAR = "REGULAR", "Regular"
        AD_HOC = "AD_HOC", "Ad-Hoc"

    class State(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        SIGNED_OFF = "SIGNED_OFF", "Signed Off"
        REOPENED = "REOPENED", "Reopened"

    vessel_id = models.CharField(max_length=64)
    scm_number = models.CharField(max_length=48, unique=True)
    meeting_type = models.CharField(
        max_length=16,
        choices=MeetingType.choices,
        default=MeetingType.REGULAR,
    )
    meeting_date = models.DateField()
    meeting_time_local = models.TimeField()
    occasion = models.CharField(max_length=8, default="M")
    ship_position = models.CharField(max_length=1, default="P")
    ship_pos_from = models.CharField(max_length=128, null=True, blank=True)
    ship_pos_to = models.CharField(max_length=128, null=True, blank=True)
    comm_time = models.TimeField(null=True, blank=True)
    comp_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=128, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    voyage_no = models.CharField(max_length=32, null=True, blank=True)
    chair_crew_id = models.CharField(max_length=64)
    prepared_by_crew_id = models.CharField(max_length=64)
    ad_hoc_trigger_reason = models.TextField(null=True, blank=True)
    office_comment = models.TextField(null=True, blank=True)
    office_comment_by = models.CharField(max_length=64, null=True, blank=True)
    office_comment_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(
        max_length=24,
        choices=State.choices,
        default=State.DRAFT,
    )
    master_signed_off_at = models.DateTimeField(null=True, blank=True)
    master_signed_off_by = models.CharField(max_length=64, null=True, blank=True)
    attendance_warnings_acknowledged_at = models.DateTimeField(null=True, blank=True)
    attendance_warnings_acknowledged_by = models.CharField(max_length=64, null=True, blank=True)
    pdf_export_path = models.CharField(max_length=512, null=True, blank=True)
    schema_version = models.IntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_scm_meeting"
        ordering = ("-meeting_date", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(meeting_type__in=["REGULAR", "AD_HOC"]),
                name="ck_vims_safety_scm_meeting_type",
            ),
            models.CheckConstraint(
                condition=Q(state__in=["DRAFT", "SUBMITTED", "SIGNED_OFF", "REOPENED"]),
                name="ck_vims_safety_scm_meeting_state",
            ),
            models.CheckConstraint(
                condition=Q(ship_position__in=["S", "P"]),
                name="ck_vims_safety_scm_ship_position",
            ),
            models.CheckConstraint(
                condition=~Q(meeting_type="AD_HOC") | Q(ad_hoc_trigger_reason__isnull=False),
                name="ck_vims_safety_scm_meeting_adhoc_reason",
            ),
            models.CheckConstraint(
                condition=(Q(is_archived=False) & Q(archived_at__isnull=True))
                | (Q(is_archived=True) & Q(archived_at__isnull=False)),
                name="ck_vims_safety_scm_meeting_archive_pair",
            ),
        ]
        indexes = [
            models.Index(fields=("vessel_id", "meeting_date"), name="ix_safe_scmm_vsl_dt"),
            models.Index(fields=("state",), name="ix_safe_scmm_state"),
            models.Index(fields=("meeting_type", "meeting_date"), name="ix_safe_scmm_type"),
        ]


class SCMAttendance(PublicIdMixin):
    meeting_id = models.BigIntegerField()
    crew_id = models.CharField(max_length=64)
    rank_name = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128)
    present = models.BooleanField(default=True)
    absence_reason = models.TextField(null=True, blank=True)
    wrh_data_available = models.BooleanField(default=True)
    wrh_rest_hours_24h = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    wrh_rest_hours_7d = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    wrh_non_compliance_flag = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    schema_version = models.IntegerField(default=1)

    class Meta:
        db_table = "vims_safety_scm_attendance"
        constraints = [
            models.UniqueConstraint(fields=("meeting_id", "crew_id"), name="uq_vims_safety_scm_attendance"),
        ]
        indexes = [
            models.Index(fields=("meeting_id",), name="ix_safe_scmt_meet"),
            models.Index(fields=("crew_id",), name="ix_safe_scmt_crew"),
        ]


class SCMSignature(PublicIdMixin):
    class SignerRole(models.TextChoices):
        MASTER = "MASTER", "Master"
        CO = "CO", "Chief Officer"
        ATTENDEE = "ATTENDEE", "Attendee"

    meeting_id = models.BigIntegerField()
    signer_role = models.CharField(max_length=16, choices=SignerRole.choices)
    signer_crew_id = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128)
    typed_name = models.CharField(max_length=128)
    device_fingerprint = models.CharField(max_length=128)
    signed_at = models.DateTimeField()
    created_by = models.CharField(max_length=128)
    schema_version = models.IntegerField(default=1)

    class Meta:
        db_table = "vims_safety_scm_signature"
        constraints = [
            models.UniqueConstraint(
                fields=("meeting_id", "signer_role", "signer_crew_id"),
                name="uq_vims_safety_scm_signature",
            ),
        ]
        indexes = [
            models.Index(fields=("meeting_id",), name="ix_safe_scms_meet"),
            models.Index(fields=("signer_role",), name="ix_safe_scms_role"),
        ]


class SCMAgendaItem(PublicIdMixin):
    meeting_id = models.BigIntegerField()
    agenda_item_number = models.IntegerField()
    section_label = models.CharField(max_length=128)
    auto_populated = models.BooleanField(default=False)
    content = models.TextField()
    decision = models.TextField(null=True, blank=True)
    linked_finding_ids = models.TextField(null=True, blank=True)
    linked_incident_ids = models.TextField(null=True, blank=True)
    schema_version = models.IntegerField(default=1)

    class Meta:
        db_table = "vims_safety_scm_agenda"
        ordering = ("agenda_item_number", "id")
        constraints = [
            models.UniqueConstraint(fields=("meeting_id", "agenda_item_number"), name="uq_vims_safety_scm_agenda_item"),
        ]
        indexes = [
            models.Index(fields=("meeting_id", "agenda_item_number"), name="ix_safe_scma_meet"),
        ]


class SCMLegacyField(PublicIdMixin):
    class FieldType(models.TextChoices):
        BOOLEAN = "BOOLEAN", "Boolean"
        DATE = "DATE", "Date"
        INTEGER = "INTEGER", "Integer"
        TEXT = "TEXT", "Text"

    meeting_id = models.BigIntegerField()
    agenda_item_number = models.IntegerField()
    field_key = models.CharField(max_length=64)
    field_label = models.CharField(max_length=160)
    field_type = models.CharField(max_length=16, choices=FieldType.choices, default=FieldType.TEXT)
    field_value = models.TextField(null=True, blank=True)
    schema_version = models.IntegerField(default=1)

    class Meta:
        db_table = "vims_safety_scm_legacy_field"
        ordering = ("agenda_item_number", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("meeting_id", "agenda_item_number", "field_key"),
                name="uq_vims_safety_scm_legacy_field",
            ),
            models.CheckConstraint(
                condition=Q(agenda_item_number__gte=1) & Q(agenda_item_number__lte=10),
                name="ck_vims_safety_scm_legacy_section",
            ),
            models.CheckConstraint(
                condition=Q(field_type__in=["BOOLEAN", "DATE", "INTEGER", "TEXT"]),
                name="ck_vims_safety_scm_legacy_type",
            ),
        ]
        indexes = [
            models.Index(fields=("meeting_id", "agenda_item_number"), name="ix_safe_scml_meet_sec"),
        ]
