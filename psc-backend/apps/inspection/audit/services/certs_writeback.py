"""Certs writeback outbox for external-audit close-out."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Protocol

from django.utils import timezone

from apps.inspection.audit.models import AuditDetail, CertWritebackOutbox
from apps.inspection.audit.services.cert_reader import get_cert_snapshot


SENT = "SENT"
QUEUED = "QUEUED"
CONFLICT = "CONFLICT"
DEAD_LETTER = "DEAD_LETTER"
DEAD_LETTER_AFTER_HOURS = 24
CERT_STATUS_BY_IMPACT = {
    "NONE": None,
    "CERT_VALID": "ok",
    "RENEWAL_AT_RISK": "at_risk",
    "SUSPENDED": "suspended",
    "WITHDRAWN": "withdrawn",
}


@dataclass(frozen=True)
class DrainResult:
    sent: int = 0
    conflict: int = 0
    dead_letter: int = 0
    retry: int = 0


class CertWritebackRepository(Protocol):
    def create_item(self, values: dict[str, Any], *, actor_id: str) -> dict[str, Any]: ...

    def apply_audit_writeback(
        self,
        tracked_item_id: str,
        values: dict[str, Any],
        *,
        actor_id: str,
        source_ref: str,
        expected_version: int,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]: ...


def enqueue_external_close_writebacks(
    *,
    audit_detail: AuditDetail,
    user,
    repository=None,
) -> list[CertWritebackOutbox]:
    if audit_detail.audit_classification != "EXTERNAL":
        return []

    cert_ids = _csv_to_list(audit_detail.linked_cert_ids_csv)
    if not cert_ids:
        return []

    rows: list[CertWritebackOutbox] = []
    for cert_id in cert_ids:
        snapshot = get_cert_snapshot(cert_id, repository=repository)
        if snapshot is None:
            if _is_initial_subtype(audit_detail):
                rows.append(
                    _create_outbox_row(
                        audit_detail=audit_detail,
                        vessel_cert_id=cert_id,
                        payload=_payload_for_initial_create(audit_detail=audit_detail, cert_id=cert_id),
                        expected_version=0,
                        created_by=_actor_id(user),
                        status=QUEUED,
                    )
                )
                continue
            rows.append(
                _create_outbox_row(
                    audit_detail=audit_detail,
                    vessel_cert_id=cert_id,
                    payload=_payload_for_missing_cert(audit_detail=audit_detail, cert_id=cert_id),
                    expected_version=0,
                    created_by=_actor_id(user),
                    status=CONFLICT,
                    last_error="Linked Certs row was not found at external close-out.",
                )
            )
            continue

        rows.append(
            _create_outbox_row(
                audit_detail=audit_detail,
                vessel_cert_id=cert_id,
                payload=_payload_for_snapshot(audit_detail=audit_detail, snapshot=snapshot),
                expected_version=snapshot.version,
                created_by=_actor_id(user),
                status=QUEUED,
            )
        )
    return rows


def drain_cert_writeback_outbox(
    *,
    repository: CertWritebackRepository,
    limit: int = 100,
    now=None,
) -> DrainResult:
    current_time = now or timezone.now()
    result = {"sent": 0, "conflict": 0, "dead_letter": 0, "retry": 0}
    rows = list(
        CertWritebackOutbox.objects.filter(status=QUEUED).order_by("created_date", "id")[: max(1, int(limit))]
    )

    for row in rows:
        try:
            payload = json.loads(row.writeback_payload)
            if payload.get("operation") == "CREATE_CERT":
                if not hasattr(repository, "create_item"):
                    _mark_retry_or_dead_letter(row, "Certs repository cannot create tracked items.", current_time)
                    result["dead_letter" if row.status == DEAD_LETTER else "retry"] += 1
                    continue
                repository.create_item(payload.get("cert_update") or {}, actor_id=row.created_by or "audit-writeback")
                row.status = SENT
                row.last_error = None
                row.updated_date = current_time
                row.save(update_fields=["status", "last_error", "updated_date"])
                result["sent"] += 1
                continue
            before, _after, applied = repository.apply_audit_writeback(
                str(row.vessel_cert_id),
                payload.get("cert_update") or {},
                actor_id=row.created_by or "audit-writeback",
                source_ref=f"audit_detail:{row.audit_detail_id}",
                expected_version=int(row.expected_cert_version),
            )
            if before is not None and not applied:
                _mark_conflict(row, "Certs version changed before writeback drained.")
                result["conflict"] += 1
                continue
            if before is None:
                _mark_retry_or_dead_letter(row, "Linked Certs row no longer exists.", current_time)
                result["dead_letter" if row.status == DEAD_LETTER else "retry"] += 1
                continue

            row.status = SENT
            row.last_error = None
            row.updated_date = current_time
            row.save(update_fields=["status", "last_error", "updated_date"])
            result["sent"] += 1
        except Exception as exc:  # pragma: no cover - exact DB adapter errors vary.
            _mark_retry_or_dead_letter(row, str(exc), current_time)
            result["dead_letter" if row.status == DEAD_LETTER else "retry"] += 1

    return DrainResult(**result)


def _payload_for_snapshot(*, audit_detail: AuditDetail, snapshot) -> dict[str, Any]:
    impact = audit_detail.certificate_impact or "NONE"
    cert_update: dict[str, Any] = {
        "lastDoneDate": _iso(audit_detail.audit_end_date or audit_detail.audit_start_date),
    }
    if _is_interim_subtype(audit_detail):
        cert_update["lifecycleStatus"] = "active"
    if audit_detail.is_cycle_resetting:
        cert_update["anniversaryDate"] = _iso(audit_detail.audit_end_date or audit_detail.audit_start_date)
    status = CERT_STATUS_BY_IMPACT.get(impact)
    if status:
        cert_update["status"] = status

    return {
        "schema": "audit.certs.writeback.v1",
        "auditDetailId": str(audit_detail.id),
        "auditDate": _iso(audit_detail.audit_end_date or audit_detail.audit_start_date),
        "auditSubtype": audit_detail.audit_subtype,
        "externalAuditSubtypes": _csv_to_list(audit_detail.external_audit_subtypes_csv),
        "certificateImpact": impact,
        "certSnapshot": {
            "version": snapshot.version,
            "anniversaryDate": _iso(snapshot.anniversary_date),
            "windowOpen": _iso(snapshot.window_open),
            "windowClose": _iso(snapshot.window_close),
            "issueDate": _iso(snapshot.issue_date),
            "expiryDate": _iso(snapshot.expiry_date),
            "lastDoneDate": _iso(snapshot.last_done_date),
            "nextDueDate": _iso(snapshot.next_due_date),
            "status": snapshot.status,
            "lifecycleStatus": snapshot.lifecycle_status,
        },
        "cert_update": cert_update,
    }


def _payload_for_initial_create(*, audit_detail: AuditDetail, cert_id: str) -> dict[str, Any]:
    audit_date = audit_detail.audit_end_date or audit_detail.audit_start_date
    return {
        "schema": "audit.certs.writeback.v1",
        "operation": "CREATE_CERT",
        "auditDetailId": str(audit_detail.id),
        "requestedCertId": cert_id,
        "auditDate": _iso(audit_date),
        "auditSubtype": audit_detail.audit_subtype,
        "externalAuditSubtypes": _csv_to_list(audit_detail.external_audit_subtypes_csv),
        "certificateImpact": audit_detail.certificate_impact or "NONE",
        "cert_update": {
            "vesselId": audit_detail.vessel_id,
            "anniversaryDate": _iso(audit_date),
            "lastDoneDate": _iso(audit_date),
            "status": CERT_STATUS_BY_IMPACT.get(audit_detail.certificate_impact or "NONE") or "ok",
            "source": "audit",
            "approvalState": "approved",
            "lifecycleStatus": "active",
        },
    }


def _payload_for_missing_cert(*, audit_detail: AuditDetail, cert_id: str) -> dict[str, Any]:
    return {
        "schema": "audit.certs.writeback.v1",
        "auditDetailId": str(audit_detail.id),
        "auditDate": _iso(audit_detail.audit_end_date or audit_detail.audit_start_date),
        "missingCertId": cert_id,
        "certificateImpact": audit_detail.certificate_impact or "NONE",
        "cert_update": {},
    }


def _create_outbox_row(
    *,
    audit_detail: AuditDetail,
    vessel_cert_id: str,
    payload: dict[str, Any],
    expected_version: int,
    created_by: str,
    status: str,
    last_error: str | None = None,
) -> CertWritebackOutbox:
    return CertWritebackOutbox.objects.create(
        audit_detail_id=audit_detail.id,
        vessel_cert_id=vessel_cert_id,
        writeback_payload=json.dumps(payload, sort_keys=True),
        expected_cert_version=expected_version,
        status=status,
        last_error=last_error,
        created_by=created_by,
    )


def _mark_conflict(row: CertWritebackOutbox, message: str) -> None:
    row.status = CONFLICT
    row.last_error = message
    row.updated_date = timezone.now()
    row.save(update_fields=["status", "last_error", "updated_date"])


def _mark_retry_or_dead_letter(row: CertWritebackOutbox, message: str, now) -> None:
    row.attempt_count += 1
    row.last_error = message
    row.updated_date = now
    if row.created_date and now - row.created_date >= timedelta(hours=DEAD_LETTER_AFTER_HOURS):
        row.status = DEAD_LETTER
        row.dead_lettered_at = now
        row.save(
            update_fields=[
                "attempt_count",
                "last_error",
                "updated_date",
                "status",
                "dead_lettered_at",
            ]
        )
        return
    row.save(update_fields=["attempt_count", "last_error", "updated_date"])


def _csv_to_list(value: str | None) -> list[str]:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def _actor_id(user) -> str:
    return str(getattr(user, "id", None) or getattr(user, "username", None) or "audit-writeback")


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _audit_subtypes(audit_detail: AuditDetail) -> set[str]:
    values = _csv_to_list(audit_detail.external_audit_subtypes_csv)
    values.append(audit_detail.audit_subtype)
    return {value for value in values if value}


def _is_initial_subtype(audit_detail: AuditDetail) -> bool:
    return any(value.endswith("_INITIAL") for value in _audit_subtypes(audit_detail))


def _is_interim_subtype(audit_detail: AuditDetail) -> bool:
    return any(value.endswith("_INTERIM") for value in _audit_subtypes(audit_detail))
