"""External-audit close-out services for Phase 11.3."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.inspection.audit.models import (
    AuditAttachment,
    AuditDetail,
    AuditFinding,
    AuditFindingNC,
    AuditFindingOBS,
    CertWritebackOutbox,
    FlagStateNotificationLog,
)
from apps.inspection.audit.services.cert_reader import get_cert_snapshot
from apps.inspection.audit.services.certs_writeback import enqueue_external_close_writebacks


logger = logging.getLogger(__name__)

CERTIFICATE_IMPACTS = {"NONE", "CERT_VALID", "RENEWAL_AT_RISK", "SUSPENDED", "WITHDRAWN"}
INITIAL_SUBTYPES = {"DOC_INITIAL", "SMC_INITIAL", "MLC_INITIAL", "ISPS_INITIAL"}
INTERIM_SUBTYPES = {"DOC_INTERIM", "SMC_INTERIM", "MLC_INTERIM", "ISPS_INTERIM"}


class ExternalCloseoutError(ValueError):
    def __init__(self, message: str, *, error: str = "EXTERNAL_CLOSEOUT_ERROR", status_code: int = 400):
        super().__init__(message)
        self.error = error
        self.status_code = status_code


@dataclass(frozen=True)
class ExternalCloseoutResult:
    audit_detail: AuditDetail
    outbox_rows: list[CertWritebackOutbox]
    flag_notification: FlagStateNotificationLog | None = None


@transaction.atomic
def confirm_external_audit_closeout(
    *,
    audit_detail: AuditDetail,
    data: dict[str, Any],
    user,
    repository=None,
) -> ExternalCloseoutResult:
    """Validate and record audit-level external close-out inputs."""

    _require_external_audit(audit_detail)
    impact = _required_impact(data.get("certificate_impact"))
    _require_external_closeout_letter(audit_detail)
    _apply_cycle_reset_inputs(audit_detail=audit_detail, data=data, user=user)
    _validate_initial_anniversary_lifecycle(audit_detail=audit_detail, repository=repository)

    flag_notification = None
    if impact == "SUSPENDED":
        _validate_suspension_confirmation(audit_detail=audit_detail, data=data, repository=repository)
        flag_notification = _create_flag_notification(audit_detail=audit_detail, data=data, user=user)

    _apply_external_effrev_tiers(audit_detail=audit_detail, user=user)

    audit_detail.certificate_impact = impact
    audit_detail.external_closure_status = "EXTERNAL_AUDITOR_CLOSED"
    audit_detail.status = "DPA_CLOSED"
    audit_detail.updated_by = _actor_id(user)
    audit_detail.updated_date = timezone.now()
    update_fields = [
            "certificate_impact",
            "external_closure_status",
            "status",
            "updated_by",
            "updated_date",
    ]
    if audit_detail.is_cycle_resetting:
        update_fields.extend([
            "is_cycle_resetting",
            "cycle_reset_reason",
            "cycle_reset_authorised_by",
            "cycle_reset_authorised_at",
        ])
    audit_detail.save(update_fields=update_fields)

    try:
        outbox_rows = enqueue_external_close_writebacks(
            audit_detail=audit_detail,
            user=user,
            repository=repository,
        )
    except Exception:
        logger.exception("Audit external Certs writeback enqueue failed for audit_detail=%s", audit_detail.id)
        outbox_rows = []

    return ExternalCloseoutResult(
        audit_detail=audit_detail,
        outbox_rows=outbox_rows,
        flag_notification=flag_notification,
    )


@transaction.atomic
def amend_external_cert_links(
    *,
    audit_detail: AuditDetail,
    linked_cert_ids: list[str],
    reason: str,
    user,
    repository=None,
) -> list[CertWritebackOutbox]:
    _require_external_audit(audit_detail)
    if audit_detail.external_closure_status != "EXTERNAL_AUDITOR_CLOSED":
        raise ExternalCloseoutError(
            "Cert link edits are allowed only after external audit close-out.",
            error="NOT_CLOSED",
            status_code=409,
        )
    if len((reason or "").strip()) < 50:
        raise ExternalCloseoutError(
            "Post-closure cert link edit reason must be at least 50 characters.",
            error="REASON_TOO_SHORT",
        )

    audit_detail.linked_cert_ids_csv = ",".join(linked_cert_ids) or None
    audit_detail.updated_by = _actor_id(user)
    audit_detail.updated_date = timezone.now()
    audit_detail.save(update_fields=["linked_cert_ids_csv", "updated_by", "updated_date"])
    return enqueue_external_close_writebacks(audit_detail=audit_detail, user=user, repository=repository)


def _require_external_audit(audit_detail: AuditDetail) -> None:
    if audit_detail.audit_classification != "EXTERNAL":
        raise ExternalCloseoutError(
            "Certificate impact and external close-out are valid only for EXTERNAL audits.",
            error="NOT_EXTERNAL_AUDIT",
            status_code=409,
        )


def _required_impact(value: object) -> str:
    impact = str(value or "").strip().upper()
    if not impact:
        raise ExternalCloseoutError("certificate_impact is mandatory at external close-out.", error="IMPACT_REQUIRED")
    if impact not in CERTIFICATE_IMPACTS:
        raise ExternalCloseoutError("certificate_impact is not a supported value.", error="IMPACT_INVALID")
    return impact


def _require_external_closeout_letter(audit_detail: AuditDetail) -> None:
    if not AuditAttachment.objects.filter(
        audit_detail_id=audit_detail.id,
        category="EXTERNAL_CLOSE_OUT_LETTER",
    ).exists():
        raise ExternalCloseoutError(
            "External close-out letter is required before external closure.",
            error="LETTER_REQUIRED",
        )


def _apply_cycle_reset_inputs(*, audit_detail: AuditDetail, data: dict[str, Any], user) -> None:
    if not data.get("is_cycle_resetting"):
        return
    reason = str(data.get("cycle_reset_reason") or "").strip()
    if len(reason) < 100:
        raise ExternalCloseoutError(
            "cycle_reset_reason must be at least 100 characters when is_cycle_resetting is true.",
            error="CYCLE_RESET_REASON_TOO_SHORT",
        )
    audit_detail.is_cycle_resetting = True
    audit_detail.cycle_reset_reason = reason
    audit_detail.cycle_reset_authorised_by = _actor_id(user)
    audit_detail.cycle_reset_authorised_at = timezone.now()


def _validate_suspension_confirmation(*, audit_detail: AuditDetail, data: dict[str, Any], repository=None) -> None:
    typed = str(data.get("typed_cert_number") or "").strip()
    if not typed:
        raise ExternalCloseoutError(
            "SUSPENDED impact requires typed cert-number confirmation.",
            error="CERT_CONFIRMATION_REQUIRED",
        )

    cert_ids = _csv_to_list(audit_detail.linked_cert_ids_csv)
    acceptable = set(cert_ids)
    for cert_id in cert_ids:
        snapshot = get_cert_snapshot(cert_id, repository=repository)
        certificate_number = getattr(snapshot, "certificate_number", None) if snapshot is not None else None
        if certificate_number:
            acceptable.add(str(certificate_number))
    if typed not in acceptable:
        raise ExternalCloseoutError(
            "Typed certificate confirmation does not match a linked certificate.",
            error="CERT_CONFIRMATION_MISMATCH",
        )


def _validate_initial_anniversary_lifecycle(*, audit_detail: AuditDetail, repository=None) -> None:
    if not _is_initial_subtype(audit_detail):
        return
    for cert_id in _csv_to_list(audit_detail.linked_cert_ids_csv):
        if get_cert_snapshot(cert_id, repository=repository) is not None:
            raise ExternalCloseoutError(
                "Initial audit close-out found an existing linked Certs row; DPA reconciliation is required.",
                error="INITIAL_CERT_EXISTS",
                status_code=409,
            )


def _create_flag_notification(*, audit_detail: AuditDetail, data: dict[str, Any], user) -> FlagStateNotificationLog:
    notified_to = str(data.get("flag_notified_to") or "").strip()
    notification_ref = str(data.get("flag_notification_ref") or "").strip()
    if not notified_to or not notification_ref:
        raise ExternalCloseoutError(
            "SUSPENDED impact requires flag-state notification recipient and reference.",
            error="FLAG_NOTIFICATION_REQUIRED",
        )
    return FlagStateNotificationLog.objects.create(
        audit_detail_id=audit_detail.id,
        notified_at=timezone.now(),
        notified_to=notified_to,
        notification_ref=notification_ref,
        created_by=_actor_id(user),
    )


def _apply_external_effrev_tiers(*, audit_detail: AuditDetail, user) -> None:
    findings = AuditFinding.objects.filter(audit_detail_id=audit_detail.id, is_external=True)
    now = timezone.now()
    for finding in findings:
        if finding.finding_type == "OBSERVATION":
            AuditFindingOBS.objects.filter(audit_finding_id=finding.id).update(updated_by=_actor_id(user), updated_date=now)
            continue
        if finding.finding_type != "NC":
            continue
        nc, _created = AuditFindingNC.objects.get_or_create(
            audit_finding_id=finding.id,
            defaults={"created_by": _actor_id(user)},
        )
        nc.is_external_tier = "MAJOR_MANDATORY" if finding.nc_category == "MAJOR_NC" else "MINOR_OPTIONAL"
        if finding.nc_category == "MAJOR_NC" and nc.effectiveness_review_date is None:
            base_date = audit_detail.audit_end_date or audit_detail.audit_start_date
            nc.effectiveness_review_date = base_date + timedelta(days=90)
        nc.updated_by = _actor_id(user)
        nc.updated_date = now
        nc.save(update_fields=["is_external_tier", "effectiveness_review_date", "updated_by", "updated_date"])


def _csv_to_list(value: str | None) -> list[str]:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def _is_initial_subtype(audit_detail: AuditDetail) -> bool:
    values = _csv_to_list(audit_detail.external_audit_subtypes_csv)
    values.append(audit_detail.audit_subtype)
    return any(value.endswith("_INITIAL") for value in values)


def _actor_id(user) -> str:
    return str(getattr(user, "id", None) or getattr(user, "username", None) or "audit-closeout")
