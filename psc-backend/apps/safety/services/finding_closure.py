from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.safety.models import SOIFinding, SOIInspection, SafetyFieldHistory

from .field_history_recorder import (
    capture_model_state,
    record_field_changes,
    resolve_actor_id,
    resolve_actor_role,
)
from .repeat_finding_detector import RepeatFindingDetector
from .signature_chain import SignatureChainService


PENDING_CLOSURE_ROLES = {"SO", "CO", "CHIEF OFFICER", "2E", "2/E", "SECOND ENGINEER"}
MASTER_ROLES = {"MASTER"}
DPA_ROLES = {"DPA"}


class FindingClosureService:
    def __init__(
        self,
        *,
        repeat_detector: RepeatFindingDetector | None = None,
        signature_service: SignatureChainService | None = None,
    ) -> None:
        self.repeat_detector = repeat_detector or RepeatFindingDetector()
        self.signature_service = signature_service or SignatureChainService()

    def mark_pending_closure(
        self,
        *,
        finding: SOIFinding,
        user,
        typed_name: str,
        device_fingerprint: str,
        closure_note: str | None = None,
    ) -> dict[str, object]:
        self._assert_pending_actor(user)
        if finding.status not in {SOIFinding.Status.OPEN, SOIFinding.Status.CARRIED_FORWARD}:
            raise ValidationError("Only open or carried-forward SOI findings can move to pending closure.")

        signature = self.signature_service.validate_payload(
            typed_name=typed_name,
            device_fingerprint=device_fingerprint,
        )
        actor_id = resolve_actor_id(user)
        note = (closure_note or "").strip() or None

        with transaction.atomic():
            old_state = capture_model_state(
                finding,
                field_names=("status", "closure_note", "updated_by", "updated_date"),
            )
            finding.status = SOIFinding.Status.PENDING_CLOSURE
            finding.closure_note = self._append_note(
                existing_note=finding.closure_note,
                prefix="SO pending closure",
                note=note,
            )
            finding.updated_by = actor_id
            finding.updated_date = signature.signed_at
            finding.save(update_fields=("status", "closure_note", "updated_by", "updated_date"))
            record_field_changes(
                finding,
                old_state,
                user=user,
                field_names=("status", "closure_note", "updated_by", "updated_date"),
                change_reason=note or "SO marked finding pending closure.",
            )
            self._record_signature(
                finding=finding,
                field_name="soi_pending_closure_signature",
                signature=signature,
                user=user,
            )

        return {
            "finding_id": finding.pk,
            "status": finding.status,
            "transition": "PENDING_CLOSURE",
        }

    def approve_closure(
        self,
        *,
        finding: SOIFinding,
        user,
        typed_name: str,
        device_fingerprint: str,
        closure_note: str | None = None,
    ) -> dict[str, object]:
        self._assert_master_actor(user)
        if finding.status != SOIFinding.Status.PENDING_CLOSURE:
            raise ValidationError("Only pending-closure SOI findings can be approved for closure.")

        signature = self.signature_service.validate_payload(
            typed_name=typed_name,
            device_fingerprint=device_fingerprint,
        )
        actor_id = resolve_actor_id(user)
        note = (closure_note or "").strip() or None

        with transaction.atomic():
            approval_state = capture_model_state(
                finding,
                field_names=(
                    "status",
                    "master_approved_at",
                    "master_approved_by",
                    "closure_note",
                    "updated_by",
                    "updated_date",
                ),
            )
            finding.status = SOIFinding.Status.MASTER_APPROVED
            finding.master_approved_at = signature.signed_at
            finding.master_approved_by = actor_id
            finding.closure_note = self._append_note(
                existing_note=finding.closure_note,
                prefix="Master approved closure",
                note=note,
            )
            finding.updated_by = actor_id
            finding.updated_date = signature.signed_at
            finding.save(
                update_fields=(
                    "status",
                    "master_approved_at",
                    "master_approved_by",
                    "closure_note",
                    "updated_by",
                    "updated_date",
                )
            )
            record_field_changes(
                finding,
                approval_state,
                user=user,
                field_names=(
                    "status",
                    "master_approved_at",
                    "master_approved_by",
                    "closure_note",
                    "updated_by",
                    "updated_date",
                ),
                change_reason=note or "Master approved finding closure.",
            )
            self._record_signature(
                finding=finding,
                field_name="soi_master_counter_signature",
                signature=signature,
                user=user,
            )
            self._record_metadata(
                finding=finding,
                field_name="master_approval_state",
                value="MASTER_APPROVED",
                user=user,
            )
            close_state = capture_model_state(
                finding,
                field_names=("status", "closed_at", "updated_by", "updated_date"),
            )
            finding.status = SOIFinding.Status.CLOSED
            finding.closed_at = signature.signed_at
            finding.updated_by = actor_id
            finding.updated_date = signature.signed_at
            finding.save(update_fields=("status", "closed_at", "updated_by", "updated_date"))
            record_field_changes(
                finding,
                close_state,
                user=user,
                field_names=("status", "closed_at", "updated_by", "updated_date"),
                change_reason=note or "Master closed finding after approval.",
            )

        repeat_result = self.repeat_detector.detect(finding, reference_at=finding.closed_at)
        return {
            "finding_id": finding.pk,
            "status": finding.status,
            "transition": "APPROVED_AND_CLOSED",
            "repeat": repeat_result.to_payload(),
        }

    def reject_closure(self, *, finding: SOIFinding, user, reason: str) -> dict[str, object]:
        self._assert_master_actor(user)
        if finding.status != SOIFinding.Status.PENDING_CLOSURE:
            raise ValidationError("Only pending-closure SOI findings can be rejected back to open.")

        normalized_reason = (reason or "").strip()
        if not normalized_reason:
            raise ValidationError({"reason": "Master rejection requires a written reason."})

        with transaction.atomic():
            old_state = capture_model_state(
                finding,
                field_names=("status", "closure_note", "updated_by", "updated_date"),
            )
            finding.status = SOIFinding.Status.OPEN
            finding.closure_note = self._append_note(
                existing_note=finding.closure_note,
                prefix="Master rejection",
                note=normalized_reason,
            )
            finding.updated_by = resolve_actor_id(user)
            finding.updated_date = timezone.now()
            finding.save(update_fields=("status", "closure_note", "updated_by", "updated_date"))
            record_field_changes(
                finding,
                old_state,
                user=user,
                field_names=("status", "closure_note", "updated_by", "updated_date"),
                change_reason=normalized_reason,
            )
            self._record_metadata(
                finding=finding,
                field_name="master_rejection_reason",
                value=normalized_reason,
                user=user,
            )

        return {
            "finding_id": finding.pk,
            "status": finding.status,
            "transition": "REJECTED_TO_OPEN",
            "reason": normalized_reason,
        }

    def reopen_closed_finding(self, *, finding: SOIFinding, user, reason: str) -> dict[str, object]:
        self._assert_dpa_actor(user)
        if finding.status not in {SOIFinding.Status.CLOSED, SOIFinding.Status.MASTER_APPROVED}:
            raise ValidationError("Only closed or Master-approved SOI findings can be reopened by DPA.")

        normalized_reason = (reason or "").strip()
        if not normalized_reason:
            raise ValidationError({"reason": "DPA reopen requires a written reason."})

        with transaction.atomic():
            old_state = capture_model_state(
                finding,
                field_names=(
                    "status",
                    "closed_at",
                    "master_approved_at",
                    "master_approved_by",
                    "closure_note",
                    "updated_by",
                    "updated_date",
                ),
            )
            finding.status = SOIFinding.Status.OPEN
            finding.closed_at = None
            finding.master_approved_at = None
            finding.master_approved_by = None
            finding.closure_note = self._append_note(
                existing_note=finding.closure_note,
                prefix="DPA reopened finding",
                note=normalized_reason,
            )
            finding.updated_by = resolve_actor_id(user)
            finding.updated_date = timezone.now()
            finding.save(
                update_fields=(
                    "status",
                    "closed_at",
                    "master_approved_at",
                    "master_approved_by",
                    "closure_note",
                    "updated_by",
                    "updated_date",
                )
            )
            record_field_changes(
                finding,
                old_state,
                user=user,
                field_names=(
                    "status",
                    "closed_at",
                    "master_approved_at",
                    "master_approved_by",
                    "closure_note",
                    "updated_by",
                    "updated_date",
                ),
                change_reason=normalized_reason,
            )
            SOIInspection.objects.filter(
                pk=finding.inspection_id,
                state=SOIInspection.State.CLOSED,
                is_deleted=False,
            ).update(
                state=SOIInspection.State.REPORTED,
                closed_at=None,
                updated_by=resolve_actor_id(user),
                updated_date=timezone.now(),
            )
            self._record_metadata(
                finding=finding,
                field_name="dpa_reopen_reason",
                value=normalized_reason,
                user=user,
            )

        return {
            "finding_id": finding.pk,
            "status": finding.status,
            "transition": "DPA_REOPENED_TO_OPEN",
            "reason": normalized_reason,
        }

    def _append_note(self, *, existing_note: str | None, prefix: str, note: str | None) -> str | None:
        normalized = prefix if not note else f"{prefix}: {note}"
        if existing_note in (None, ""):
            return normalized
        return f"{existing_note}\n{normalized}"

    def _record_signature(self, *, finding: SOIFinding, field_name: str, signature, user) -> None:
        self._record_metadata(
            finding=finding,
            field_name=field_name,
            value={
                "typed_name": signature.typed_name,
                "signed_at": signature.signed_at.isoformat(),
                "device_fingerprint": signature.device_fingerprint,
                "signed_by": resolve_actor_id(user),
                "signed_role": resolve_actor_role(user),
            },
            user=user,
        )

    def _record_metadata(self, *, finding: SOIFinding, field_name: str, value, user) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=finding._meta.db_table,
            parent_id=finding.pk,
            field_name=field_name,
            old_value=None,
            new_value=value,
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=finding.schema_version or 1,
        )

    def _assert_pending_actor(self, user) -> None:
        actor_role = resolve_actor_role(user)
        if actor_role not in PENDING_CLOSURE_ROLES:
            raise PermissionDenied("Only the active Safety Officer role may mark a finding pending closure.")

    def _assert_master_actor(self, user) -> None:
        actor_role = resolve_actor_role(user)
        if actor_role not in MASTER_ROLES:
            raise PermissionDenied("Only Master may counter-sign SOI finding closure.")

    def _assert_dpa_actor(self, user) -> None:
        actor_role = resolve_actor_role(user)
        if actor_role not in DPA_ROLES:
            raise PermissionDenied("Only DPA may reopen closed SOI findings.")
