"""
Deficiency and CAR models per BACKEND_STRUCTURE.md Part 4.3, 4.4, and 4.5.

Tables:
- psc_deficiency: Individual deficiencies within an inspection
- psc_deficiency_action_history: Track action code changes
- psc_car: Corrective Action Report (placeholder, full impl in Phase 5)
"""

import uuid
import re
from django.db import connection, models
from django.utils import timezone

from .models import Inspection


class DefStatus(models.TextChoices):
    """Deficiency vessel-side workflow status. DEPRECATED — use CAR.status instead."""
    ALLOCATED = 'ALLOCATED', 'Allocated'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    APPROVED = 'APPROVED', 'Approved'
    SUBMITTED = 'SUBMITTED', 'Submitted'


class CARStatus(models.TextChoices):
    """Unified CAR workflow status covering vessel + office lifecycle."""
    DRAFT = 'DRAFT', 'Draft'
    ALLOTTED = 'ALLOTTED', 'Allotted'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    OFFICE_DRAFTED = 'OFFICE_DRAFTED', 'Office Drafted'
    PENDING_CE_REVIEW = 'PENDING_CE_REVIEW', 'Pending CE Review'
    PENDING_MASTER_REVIEW = 'PENDING_MASTER_REVIEW', 'Pending Master Review'
    SUBMITTED_TO_PIC = 'SUBMITTED_TO_PIC', 'Submitted to PIC'
    PIC_REVIEW = 'PIC_REVIEW', 'PIC Review'
    SUBMITTED_TO_LEAD_AUDITOR = 'SUBMITTED_TO_LEAD_AUDITOR', 'Submitted to Lead Auditor'
    LEAD_AUDITOR_CLOSED = 'LEAD_AUDITOR_CLOSED', 'Lead Auditor Closed'
    AWAITING_EXTERNAL_CLOSE_OUT = 'AWAITING_EXTERNAL_CLOSE_OUT', 'Awaiting External Close Out'
    EXTERNAL_AUDITOR_CLOSED = 'EXTERNAL_AUDITOR_CLOSED', 'External Auditor Closed'
    SUBMITTED_TO_DPA = 'SUBMITTED_TO_DPA', 'Submitted to DPA'
    CLOSED = 'CLOSED', 'Closed'
    RETURNED_FOR_REWORK = 'RETURNED_FOR_REWORK', 'Returned for Rework'


# Backward-compat aliases for legacy code/tests that still reference old states.
CARStatus.SUBMITTED = CARStatus.SUBMITTED_TO_PIC
# Legacy alias for backward compatibility only; do not use for permissions/workflow.
CARStatus.PIC_ACCEPTED = CARStatus.PIC_REVIEW
CARStatus.REWORK_REQUESTED = CARStatus.RETURNED_FOR_REWORK
CARStatus.DPA_CLOSED = CARStatus.CLOSED


class CAR(models.Model):
    """
    Corrective Action Report - placeholder model for Phase 4.
    Full implementation in Phase 5 (FEAT-CAR-*).
    Table: psc_car

    Per BACKEND_STRUCTURE.md Part 4.5

    Note: This is a minimal model for the auto-CAR signal.
    Additional fields will be added in Phase 5.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 1:1 relationship with deficiency (set in Deficiency model)
    # deficiency field will be set via OneToOneField from Deficiency

    # CAR number: <VESSEL_CODE>-PSC-{YEAR}-{SEQ} for newly auto-created PSC CARs.
    car_number = models.CharField(max_length=20, unique=True, db_index=True)

    # Status workflow
    status = models.CharField(
        max_length=30,
        choices=CARStatus.choices,
        default=CARStatus.ALLOTTED,
        db_index=True
    )

    # Root cause (filled later in Phase 5)
    root_cause_summary = models.TextField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    initial_action_code = models.CharField(max_length=10, null=True, blank=True)

    # PIC Review fields
    pic_comment = models.TextField(null=True, blank=True)
    pic_accepted_by = models.CharField(max_length=100, null=True, blank=True)
    pic_accepted_at = models.DateTimeField(null=True, blank=True)

    # Rework fields
    rework_reason = models.TextField(null=True, blank=True)
    rework_requested_by = models.CharField(max_length=100, null=True, blank=True)
    rework_requested_at = models.DateTimeField(null=True, blank=True)
    rework_count = models.IntegerField(default=0)

    # DPA Close fields
    dpa_comment = models.TextField(null=True, blank=True)
    dpa_closed_by = models.CharField(max_length=100, null=True, blank=True)
    dpa_closed_at = models.DateTimeField(null=True, blank=True)

    # Verification pending flag (set when CAR is closed but PV not yet done)
    verification_pending = models.BooleanField(default=False)

    # Last workflow action tracking
    last_action = models.CharField(max_length=50, null=True, blank=True)
    last_action_by = models.CharField(max_length=100, null=True, blank=True)
    last_action_at = models.DateTimeField(null=True, blank=True)
    last_action_comment = models.TextField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Audit fields
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Offline sync fields
    client_id = models.UUIDField(null=True, blank=True)
    sync_version = models.IntegerField(default=1)

    class Meta:
        db_table = 'psc_car'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['car_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.car_number

    @classmethod
    def generate_car_number(cls, *, inspection: Inspection | None = None, vessel_code: str | None = None):
        """
        Generate next CAR number.

        PSC auto-created CARs use: <VESSEL_CODE>-PSC-{YEAR}-{SEQ}
        Audit auto-created CARs use: <SCOPE>-AUDIT-{YEAR}-{SEQ}
        Legacy no-context callers keep the historical PSC-{YEAR}-{SEQ} format.
        """
        current_year = timezone.now().year
        inspection_type = str(getattr(inspection, "inspection_type", "") or "").upper()
        if inspection_type == "AUDIT":
            return cls._generate_audit_car_number(
                year=current_year,
                vessel_id=getattr(inspection, "vessel_id", None),
                vessel_code=vessel_code or _lookup_vessel_code(getattr(inspection, "vessel_id", None)),
            )

        if inspection is not None or vessel_code:
            return cls._generate_vessel_car_number(
                year=current_year,
                vessel_id=getattr(inspection, "vessel_id", None),
                vessel_code=vessel_code or _lookup_vessel_code(getattr(inspection, "vessel_id", None)),
            )

        return cls._generate_legacy_car_number(year=current_year)

    @classmethod
    def _generate_legacy_car_number(cls, *, year: int) -> str:
        prefix = f"PSC-{year}-"

        last_car = cls.objects.filter(
            car_number__startswith=prefix
        ).order_by('-car_number').first()

        if last_car:
            # Extract sequence number and increment
            try:
                last_seq = int(last_car.car_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"{prefix}{next_seq:03d}"

    @classmethod
    def _generate_vessel_car_number(cls, *, year: int, vessel_id: object, vessel_code: str | None) -> str:
        normalized_code = _normalize_vessel_code(vessel_code, vessel_id=vessel_id)
        prefix = f"{normalized_code}-PSC-{year}-"
        return cls._generate_scoped_car_number(prefix=prefix)

    @classmethod
    def _generate_audit_car_number(cls, *, year: int, vessel_id: object, vessel_code: str | None) -> str:
        scope = _normalize_audit_scope(vessel_code, vessel_id=vessel_id)
        prefix = f"{scope}-AUDIT-{year}-"
        return cls._generate_scoped_car_number(prefix=prefix)

    @classmethod
    def _generate_scoped_car_number(cls, *, prefix: str) -> str:
        queryset = cls.objects.filter(car_number__startswith=prefix)

        last_seq = 0
        for car_number in queryset.values_list("car_number", flat=True):
            match = re.match(rf"^{re.escape(prefix)}(\d+)$", str(car_number or ""))
            if not match:
                continue
            last_seq = max(last_seq, int(match.group(1)))

        candidate = f"{prefix}{last_seq + 1:03d}"
        max_length = cls._meta.get_field("car_number").max_length or 20
        if len(candidate) > max_length:
            raise ValueError(
                "Generated CAR number exceeds psc_car.car_number length. "
                "A database datatype change is required before this scope/sequence can be used."
            )
        return candidate


def _normalize_vessel_code(value: str | None, *, vessel_id: object = None) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()
    if not normalized:
        raise ValueError(
            "Vessel code is required for PSC CAR numbering. "
            "Check VesselData.vesselCode for this vessel before creating a CAR."
        )
    if len(normalized) > 7:
        raise ValueError(
            "Vessel code is too long for the current psc_car.car_number length. "
            "A database datatype change is required before this code can be used."
        )
    return normalized


def _normalize_audit_scope(value: str | None, *, vessel_id: object = None) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()
    if not normalized:
        if vessel_id:
            raise ValueError(
                "Vessel code is required for Audit CAR numbering. "
                "Check VesselData.vesselCode for this vessel before creating an Audit CAR."
            )
        return "KSM"
    if len(normalized) > 5:
        raise ValueError(
            "Audit CAR scope is too long for the approved {SCOPE}-AUDIT-{YYYY}-{NNN} format. "
            "Use a vessel or office scope code of 5 characters or less."
        )
    return normalized


def _compact_uuid(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return uuid.UUID(raw).hex
    except (TypeError, ValueError, AttributeError):
        return raw.replace("-", "").lower()


def _lookup_vessel_code(vessel_id: object) -> str | None:
    if not vessel_id:
        return None
    try:
        if connection.vendor == "microsoft":
            compact_vessel_id = _compact_uuid(vessel_id)
            if not compact_vessel_id:
                return None
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TOP 1 vesselCode
                    FROM VesselData
                    WHERE id = CAST(
                        STUFF(STUFF(STUFF(STUFF(%s, 9, 0, '-'), 14, 0, '-'), 19, 0, '-'), 24, 0, '-')
                        AS uniqueidentifier
                    )
                      AND is_active = 1
                      AND is_deleted = 0
                    """,
                    [compact_vessel_id],
                )
                row = cursor.fetchone()
            return str(row[0]).strip() if row and row[0] else None

        from apps.accounts.models import VesselData
        return (
            VesselData.objects.filter(id=vessel_id)
            .values_list("vesselCode", flat=True)
            .first()
        )
    except Exception:
        return None


class Deficiency(models.Model):
    """
    Individual deficiency within an inspection.
    Table: psc_deficiency

    Per BACKEND_STRUCTURE.md Part 4.3
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK to inspection
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name='deficiencies'
    )

    # Deficiency code - store both ID reference and denormalized code for display
    # FK to PSC_Def_Code table (def_code is the PK, a 5-digit string)
    def_code_id = models.CharField(max_length=5, db_index=True)  # FK to PSC_Def_Code.def_code
    def_code = models.CharField(max_length=10)  # Denormalized for display

    # Deficiency description
    description = models.TextField()

    # Action code - store both ID reference and denormalized code
    # FK to PSC_Action_Codes table (action_code is an integer PK)
    action_code_id = models.IntegerField(null=True, blank=True, db_index=True)
    action_code = models.CharField(max_length=10, null=True, blank=True)  # Denormalized

    # Target and clearing
    target_date = models.DateField(null=True, blank=True)
    is_cleared = models.BooleanField(default=False, db_index=True)
    cleared_date = models.DateField(null=True, blank=True)

    # Follow-up reference (which follow-up inspection cleared this)
    cleared_by_follow_up = models.ForeignKey(
        Inspection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cleared_deficiencies'
    )

    # Sequence number within inspection
    sequence_no = models.IntegerField(default=1)

    # 1:1 relationship with CAR
    car = models.OneToOneField(
        CAR,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deficiency'
    )

    # Assigned crew member (who is responsible for the CAR)
    assigned_crew_id = models.CharField(null=True, blank=True, db_index=True, max_length=50)

    # Vessel-side workflow status
    def_status = models.CharField(
        max_length=20,
        choices=DefStatus.choices,
        default=DefStatus.ALLOCATED,
        db_index=True,
    )

    # Reviewer (auto-set based on owner rank)
    reviewer_crew_id = models.CharField(max_length=100, null=True, blank=True)

    # Denormalized owner/reviewer info for display
    owner_rank = models.CharField(max_length=100, null=True, blank=True)
    owner_name = models.CharField(max_length=200, null=True, blank=True)
    reviewer_rank = models.CharField(max_length=100, null=True, blank=True)
    reviewer_name = models.CharField(max_length=200, null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Audit fields
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Offline sync fields
    client_id = models.UUIDField(null=True, blank=True)
    sync_version = models.IntegerField(default=1)

    class Meta:
        db_table = 'psc_deficiency'
        ordering = ['sequence_no', 'created_date']
        indexes = [
            models.Index(fields=['inspection']),
            models.Index(fields=['def_code']),
            models.Index(fields=['is_cleared']),
            models.Index(fields=['assigned_crew_id']),
        ]

    def __str__(self):
        return f"{self.def_code} - {self.description[:50]}"

    def get_next_sequence_no(self):
        """Get the next sequence number for this inspection."""
        last_def = Deficiency.objects.filter(
            inspection=self.inspection,
            is_deleted=False
        ).order_by('-sequence_no').first()

        return (last_def.sequence_no + 1) if last_def else 1


class DeficiencyActionHistory(models.Model):
    """
    Track action code changes over time.
    Table: psc_deficiency_action_history

    Per BACKEND_STRUCTURE.md Part 4.4
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK to deficiency
    deficiency = models.ForeignKey(
        Deficiency,
        on_delete=models.CASCADE,
        related_name='action_history'
    )

    # Previous action code (null for initial)
    previous_action_code_id = models.IntegerField(null=True, blank=True)
    previous_action_code = models.CharField(max_length=10, null=True, blank=True)

    # New action code
    new_action_code_id = models.IntegerField()
    new_action_code = models.CharField(max_length=10)

    # Follow-up inspection that caused this change (if any)
    follow_up_inspection = models.ForeignKey(
        Inspection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_code_changes'
    )

    # Change metadata
    change_reason = models.CharField(max_length=500, null=True, blank=True)
    changed_by = models.CharField(max_length=100)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'psc_deficiency_action_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['deficiency']),
        ]

    def __str__(self):
        prev = self.previous_action_code or 'None'
        return f"{self.deficiency.def_code}: {prev} → {self.new_action_code}"
