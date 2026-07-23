from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any

from django.utils.dateparse import parse_datetime
from django.db import DatabaseError, connection

from apps.certs.services.notification_dispatcher import CertNotificationDispatcher, CertNotificationRecipient


logger = logging.getLogger(__name__)

RECONCILIATION_CONFIDENCE_THRESHOLD = 0.95
MISMATCH_RATE_THRESHOLD = 0.15
UNMAPPED_RATE_THRESHOLD = 0.15
UNMAPPED_CRITICAL_THRESHOLD = 0.25
PARSE_DURATION_SECONDS_THRESHOLD = 180
PARSED_ROW_COUNT_FACTOR_THRESHOLD = 0.7
PARSER_ANOMALY_TRIGGER_EVENT = "parser_anomaly"
PARSER_ANOMALY_ACTIONABLE_BUCKETS = {"mismatch", "missing_in_catalog", "unmapped_low_confidence"}
PARSER_HARD_ANOMALY_TYPES = {"parse_duration", "parsed_row_count_shortfall"}
DPA_ROLE_KEYS = {"dpa", "seqmanager", "seqmanagerdpa"}
MARINE_SUPT_ROLE_KEYS = {"marinesuperintendent", "marinesupt", "marinesuptt"}
TECH_SUPT_ROLE_KEYS = {"technicalsuperintendent", "technicalsupt", "technicalsuptt", "techsupt", "techsuptt"}
BUCKET_COUNT_COLUMNS = {
    "match": "matches_count",
    "mismatch": "mismatches_count",
    "missing_in_catalog": "missing_in_catalog_count",
    "missing_in_class": "missing_in_class_count",
    "conditional_stc": "conditional_stc_detected_count",
    "extended_postponed": "extended_postponed_detected_count",
    "unmapped_low_confidence": "unmapped_low_confidence_count",
}
COMPARABLE_FIELDS = ("certificate_number", "issue_date", "expiry_date", "last_done_date", "next_due_date", "postponed_until")
MAPPING_ELIGIBLE_BUCKETS = {"missing_in_catalog", "unmapped_low_confidence"}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReconciliationResult:
    counts: dict[str, int]
    flags: list[dict[str, Any]]
    mapping_version_used: int
    anomaly_breaches: list[dict[str, Any]]


def build_reconciliation_flags(
    *,
    parsed_payload: dict[str, Any],
    tracked_items: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
) -> ReconciliationResult:
    counts = {column: 0 for column in BUCKET_COUNT_COLUMNS.values()}
    flags: list[dict[str, Any]] = []
    mapping_by_code = {
        _normal_key(mapping.get("class_code_or_name")): mapping
        for mapping in mappings
        if mapping.get("class_code_or_name") and mapping.get("catalog_id")
    }
    tracked_by_catalog = {
        str(item.get("catalog_id")): item
        for item in tracked_items
        if item.get("catalog_id")
    }
    mapped_catalog_ids: set[str] = set()

    for class_row in _payload_rows(parsed_payload):
        class_code = _class_code(class_row)
        confidence = _confidence(class_row)
        mapping = mapping_by_code.get(_normal_key(class_code))
        if confidence < RECONCILIATION_CONFIDENCE_THRESHOLD:
            flags.append(_flag("unmapped_low_confidence", class_row=class_row, diff={"confidence": confidence}))
            counts["unmapped_low_confidence_count"] += 1
            continue
        if not mapping:
            flags.append(_flag("missing_in_catalog", class_row=class_row))
            counts["missing_in_catalog_count"] += 1
            continue

        catalog_id = str(mapping["catalog_id"])
        mapped_catalog_ids.add(catalog_id)
        tracked_item = tracked_by_catalog.get(catalog_id)
        if _is_conditional(class_row):
            flags.append(
                _flag(
                    "conditional_stc",
                    catalog_id=catalog_id,
                    tracked_item=tracked_item,
                    class_row=class_row,
                    diff={"validity_type": class_row.get("validity_type") or class_row.get("type")},
                )
            )
            counts["conditional_stc_detected_count"] += 1
            continue
        if _is_extended_or_postponed(class_row):
            flags.append(
                _flag(
                    "extended_postponed",
                    catalog_id=catalog_id,
                    tracked_item=tracked_item,
                    class_row=class_row,
                    diff={
                        "extension_of": class_row.get("extension_of"),
                        "postponed_until": class_row.get("postponed_until"),
                    },
                )
            )
            counts["extended_postponed_detected_count"] += 1
            continue
        if tracked_item is None:
            flags.append(_flag("missing_in_class", catalog_id=catalog_id, class_row=class_row))
            counts["missing_in_class_count"] += 1
            continue

        diff = _diff(class_row, tracked_item)
        if diff:
            flags.append(_flag("mismatch", catalog_id=catalog_id, tracked_item=tracked_item, class_row=class_row, diff=diff))
            counts["mismatches_count"] += 1
        else:
            flags.append(_flag("match", catalog_id=catalog_id, tracked_item=tracked_item, class_row=class_row))
            counts["matches_count"] += 1

    for tracked_item in tracked_items:
        catalog_id = str(tracked_item.get("catalog_id") or "")
        if not catalog_id or catalog_id in mapped_catalog_ids:
            continue
        if not bool(tracked_item.get("catalog_is_class_tracked")):
            continue
        flags.append(_flag("missing_in_class", catalog_id=catalog_id, tracked_item=tracked_item, class_row=None))
        counts["missing_in_class_count"] += 1

    mapping_version = max([int(mapping.get("version") or 1) for mapping in mappings] or [1])
    return ReconciliationResult(counts=counts, flags=flags, mapping_version_used=mapping_version, anomaly_breaches=[])


def evaluate_reconciliation_anomalies(
    *,
    counts: dict[str, int],
    parsed_payload: dict[str, Any],
    tracked_items: list[dict[str, Any]],
    snapshot: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    breaches: list[dict[str, Any]] = []
    total_flags = max(sum(int(counts.get(column) or 0) for column in BUCKET_COUNT_COLUMNS.values()), 0)
    if total_flags > 0:
        mismatch_count = int(counts.get("mismatches_count") or 0)
        mismatch_rate = mismatch_count / total_flags
        if mismatch_rate > MISMATCH_RATE_THRESHOLD:
            breaches.append(
                _rate_breach(
                    breach_type="mismatch_rate",
                    severity="critical",
                    count=mismatch_count,
                    total=total_flags,
                    value=mismatch_rate,
                    threshold=MISMATCH_RATE_THRESHOLD,
                    message="Mismatch rate exceeded the D-CERT-073 15% threshold.",
                )
            )

        unmapped_count = int(counts.get("missing_in_catalog_count") or 0) + int(counts.get("unmapped_low_confidence_count") or 0)
        unmapped_rate = unmapped_count / total_flags
        if unmapped_rate > UNMAPPED_RATE_THRESHOLD:
            threshold = UNMAPPED_CRITICAL_THRESHOLD if unmapped_rate > UNMAPPED_CRITICAL_THRESHOLD else UNMAPPED_RATE_THRESHOLD
            breaches.append(
                _rate_breach(
                    breach_type="unmapped_critical_rate" if unmapped_rate > UNMAPPED_CRITICAL_THRESHOLD else "unmapped_rate",
                    severity="critical" if unmapped_rate > UNMAPPED_CRITICAL_THRESHOLD else "warning",
                    count=unmapped_count,
                    total=total_flags,
                    value=unmapped_rate,
                    threshold=threshold,
                    message=(
                        "Unmapped class rows exceeded the FEAT-CERT-REC-029 25% critical threshold."
                        if unmapped_rate > UNMAPPED_CRITICAL_THRESHOLD
                        else "Unmapped class rows exceeded the OBS-CERT-04 15% anomaly threshold."
                    ),
                )
            )

    expected_class_rows = sum(1 for item in tracked_items if bool(item.get("catalog_is_class_tracked")))
    parsed_row_count = len(_payload_rows(parsed_payload))
    expected_minimum = expected_class_rows * PARSED_ROW_COUNT_FACTOR_THRESHOLD
    if expected_class_rows > 0 and parsed_row_count < expected_minimum:
        breaches.append(
            {
                "type": "parsed_row_count_shortfall",
                "severity": "critical",
                "actual": parsed_row_count,
                "expectedClassTrackedRows": expected_class_rows,
                "expectedMinimum": round(expected_minimum, 2),
                "thresholdFactor": PARSED_ROW_COUNT_FACTOR_THRESHOLD,
                "message": "Parsed row count is below expected class-tracked count x 0.7.",
            }
        )

    parse_duration_seconds = _parse_duration_seconds(snapshot or {})
    if parse_duration_seconds is not None and parse_duration_seconds > PARSE_DURATION_SECONDS_THRESHOLD:
        breaches.append(
            {
                "type": "parse_duration",
                "severity": "critical",
                "valueSeconds": parse_duration_seconds,
                "thresholdSeconds": PARSE_DURATION_SECONDS_THRESHOLD,
                "message": "Class snapshot parse duration exceeded 3 minutes.",
            }
        )
    return breaches


def should_dispatch_parser_anomaly_notifications(
    *,
    anomaly_breaches: list[dict[str, Any]],
    flags: list[dict[str, Any]],
) -> bool:
    if not anomaly_breaches:
        return False
    breach_types = {str(breach.get("type") or "") for breach in anomaly_breaches}
    if breach_types & PARSER_HARD_ANOMALY_TYPES:
        return True

    for flag in flags:
        bucket = str(flag.get("bucket") or "")
        resolved_at = flag.get("resolved_at") or flag.get("resolvedAt")
        if bucket in PARSER_ANOMALY_ACTIONABLE_BUCKETS and not resolved_at:
            return True
    return False


def parser_anomaly_recipients(
    anomaly_breaches: list[dict[str, Any]],
    *,
    candidates: list[CertNotificationRecipient] | None = None,
) -> list[CertNotificationRecipient]:
    required_groups = _parser_anomaly_required_groups(anomaly_breaches)
    recipients: list[CertNotificationRecipient] = []
    seen: set[str] = set()
    for recipient in candidates if candidates is not None else _load_default_office_recipients():
        if recipient.normalized_side() != "office":
            continue
        role_group = _parser_anomaly_role_group(recipient.role)
        if role_group not in required_groups:
            continue
        if recipient.user_id in seen:
            continue
        seen.add(recipient.user_id)
        recipients.append(recipient)
    return recipients


def dispatch_parser_anomaly_notifications(
    *,
    run: dict[str, Any],
    anomaly_breaches: list[dict[str, Any]],
    flags: list[dict[str, Any]],
    dispatcher: CertNotificationDispatcher | None = None,
    candidate_recipients: list[CertNotificationRecipient] | None = None,
) -> dict[str, Any]:
    if not should_dispatch_parser_anomaly_notifications(anomaly_breaches=anomaly_breaches, flags=flags):
        return {"dispatched": False, "reason": "suppressed_reviewed_or_empty", "recipientIds": []}

    recipients = parser_anomaly_recipients(anomaly_breaches, candidates=candidate_recipients)
    if not recipients:
        return {"dispatched": False, "reason": "no_office_recipients", "recipientIds": []}

    run_id = str(run.get("run_id") or run.get("id") or "")
    vessel_name = str(run.get("vessel_name") or run.get("vesselName") or run.get("vessel_id") or "unknown vessel")
    class_society = str(run.get("class_society") or run.get("classSociety") or "class")
    breach_labels = ", ".join(str(breach.get("type") or "unknown") for breach in anomaly_breaches)
    title = "Certs parser anomaly detected"
    message = f"{vessel_name} {class_society} reconciliation breached parser anomaly threshold(s): {breach_labels}."
    payload = {
        "eventType": PARSER_ANOMALY_TRIGGER_EVENT,
        "runId": run_id,
        "snapshotId": str(run.get("snapshot_id") or run.get("snapshotId") or ""),
        "vesselId": str(run.get("vessel_id") or run.get("vesselId") or ""),
        "vesselName": vessel_name,
        "classSociety": class_society,
        "printedOnDate": str(run.get("printed_on_date") or run.get("printedOnDate") or ""),
        "anomalyBreaches": anomaly_breaches,
    }

    try:
        result = (dispatcher or CertNotificationDispatcher()).dispatch(
            trigger_event=PARSER_ANOMALY_TRIGGER_EVENT,
            cert_row_id=None,
            vessel_id=payload["vesselId"] or None,
            recipients=recipients,
            title=title,
            message=message,
            payload=payload,
            escalation_level=1,
            idempotency_scope=f"parser-anomaly:{run_id}",
        )
    except DatabaseError as exc:
        logger.warning("Certs parser anomaly notification dispatch failed for run %s: %s", run_id, exc)
        return {
            "dispatched": False,
            "reason": "notification_dispatch_failed",
            "recipientIds": [recipient.user_id for recipient in recipients],
            "notificationsSent": [],
            "error": str(exc),
        }
    return {
        "dispatched": bool(result.notification_rows),
        "reason": "dispatched" if result.notification_rows else "already_dispatched",
        "recipientIds": [recipient.user_id for recipient in recipients],
        "notificationsSent": [
            {
                "recipientRef": row.get("recipient_ref"),
                "channel": row.get("delivery_channel"),
                "sentAt": row.get("created_at"),
            }
            for row in result.notification_rows
        ],
    }


def _rate_breach(
    *,
    breach_type: str,
    severity: str,
    count: int,
    total: int,
    value: float,
    threshold: float,
    message: str,
) -> dict[str, Any]:
    return {
        "type": breach_type,
        "severity": severity,
        "count": count,
        "total": total,
        "value": round(value, 4),
        "threshold": threshold,
        "message": message,
    }


def _parse_duration_seconds(snapshot: dict[str, Any]) -> int | None:
    started = _coerce_datetime(snapshot.get("parse_started_at") or snapshot.get("parseStartedAt"))
    completed = _coerce_datetime(snapshot.get("parse_completed_at") or snapshot.get("parseCompletedAt"))
    if started is None or completed is None:
        return None
    return max(int((completed - started).total_seconds()), 0)


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        parsed = parse_datetime(text)
        if parsed is None:
            normalized = text.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _payload_rows(parsed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = parsed_payload.get("rows")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _class_code(class_row: dict[str, Any]) -> str:
    for key in ("class_code_or_name", "classCodeOrName", "class_code", "name", "display_name"):
        value = class_row.get(key)
        if value:
            return str(value)
    return ""


def _confidence(class_row: dict[str, Any]) -> float:
    try:
        return float(class_row.get("confidence", 1.0))
    except (TypeError, ValueError):
        return 0.0


def _normal_key(value: Any) -> str:
    return str(value or "").strip().upper()


def _is_conditional(class_row: dict[str, Any]) -> bool:
    text = " ".join(str(class_row.get(key) or "") for key in ("type", "validity_type", "status")).upper()
    return bool(class_row.get("conditional")) or "CONDITIONAL" in text or "SHORT" in text or "STC" in text


def _is_extended_or_postponed(class_row: dict[str, Any]) -> bool:
    text = " ".join(str(class_row.get(key) or "") for key in ("status", "remarks")).upper()
    return bool(class_row.get("extension_of") or class_row.get("postponed_until")) or "EXTENDED" in text or "POSTPONED" in text


def _diff(class_row: dict[str, Any], tracked_item: dict[str, Any]) -> dict[str, dict[str, Any]]:
    diff: dict[str, dict[str, Any]] = {}
    for field in COMPARABLE_FIELDS:
        class_value = _empty_to_none(class_row.get(field) or class_row.get(_camelize(field)))
        tracked_value = _empty_to_none(tracked_item.get(field))
        if class_value != tracked_value:
            diff[field] = {"class": class_value, "tracked": tracked_value}
    return diff


def _empty_to_none(value: Any) -> Any:
    if value in ("", None):
        return None
    return str(value)[:32] if hasattr(value, "isoformat") else value


def _camelize(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


def _flag(
    bucket: str,
    *,
    catalog_id: str | None = None,
    tracked_item: dict[str, Any] | None = None,
    class_row: dict[str, Any] | None,
    diff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "bucket": bucket,
        "catalog_id": catalog_id,
        "tracked_item_id": str(tracked_item.get("tracked_item_id")) if tracked_item and tracked_item.get("tracked_item_id") else None,
        "class_row_extract": class_row,
        "diff": diff or {},
    }


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    rows = _fetch_all(cursor)
    return rows[0] if rows else None


def _master_message_select_sql() -> str:
    return """
        SELECT
            f.flag_id, f.run_id, f.bucket, f.catalog_id, c.display_name AS catalog_display_name,
            f.tracked_item_id, f.class_row_extract_json, f.diff_json,
            f.reviewed_by, f.reviewed_at, f.resolution_action, f.resolved_at,
            r.snapshot_id, r.ran_at,
            s.vessel_id, v.vesselName AS vessel_name, v.imoNumber AS imo_number,
            s.class_society, s.printed_on_date,
            office_review.timestamp_utc AS office_notified_at,
            office_review.actor_user_id AS office_notified_by,
            office_review.actor_role AS office_notified_role,
            office_review.reason AS office_note,
            master_review.timestamp_utc AS master_reviewed_at,
            master_review.actor_user_id AS master_reviewed_by,
            master_review.actor_role AS master_reviewed_role,
            master_review.reason AS master_review_note
        FROM dbo.vims_certs_reconciliation_flag f
        INNER JOIN dbo.vims_certs_reconciliation_run r ON r.run_id = f.run_id
        INNER JOIN dbo.vims_certs_class_status_snapshot s ON s.snapshot_id = r.snapshot_id
        LEFT JOIN dbo.VesselData v ON v.id = s.vessel_id
        LEFT JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = f.catalog_id
        OUTER APPLY (
            SELECT TOP 1
                a.timestamp_utc, a.actor_user_id, a.actor_role, a.reason
            FROM dbo.vims_certs_audit_log a
            WHERE a.entity_type = N'reconciliation_flag'
              AND a.entity_id = f.flag_id
              AND a.action = N'reconciliation_review'
              AND ISJSON(a.event_metadata) = 1
              AND JSON_VALUE(a.event_metadata, '$.resolution_action') = N'notified_master'
            ORDER BY a.timestamp_utc DESC
        ) office_review
        OUTER APPLY (
            SELECT TOP 1
                a.timestamp_utc, a.actor_user_id, a.actor_role, a.reason
            FROM dbo.vims_certs_audit_log a
            WHERE a.entity_type = N'reconciliation_flag'
              AND a.entity_id = f.flag_id
              AND a.action = N'reconciliation_review'
              AND ISJSON(a.event_metadata) = 1
              AND JSON_VALUE(a.event_metadata, '$.resolution_action') = N'master_reviewed'
            ORDER BY a.timestamp_utc DESC
        ) master_review
    """


class ReconciliationRepository:
    def list_runs(
        self,
        *,
        vessel_id: str | None = None,
        class_society: str | None = None,
        parse_status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        where = []
        params: list[Any] = []
        if vessel_id:
            where.append("s.vessel_id = %s")
            params.append(vessel_id)
        if class_society:
            where.append("s.class_society = %s")
            params.append(class_society.upper())
        if parse_status:
            where.append("s.parse_status = %s")
            params.append(parse_status)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        safe_page = max(int(page or 1), 1)
        safe_page_size = max(1, min(int(page_size or 25), 100))
        offset = (safe_page - 1) * safe_page_size
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM dbo.vims_certs_reconciliation_run r
                INNER JOIN dbo.vims_certs_class_status_snapshot s ON s.snapshot_id = r.snapshot_id
                {where_sql}
                """,
                params,
            )
            count = int(cursor.fetchone()[0] or 0)
            cursor.execute(
                f"""
                SELECT
                    r.run_id, r.snapshot_id, s.vessel_id, v.vesselName AS vessel_name,
                    v.imoNumber AS imo_number, s.class_society, s.printed_on_date,
                    s.parse_status, s.parser_version, r.ran_at,
                    r.matches_count, r.mismatches_count, r.missing_in_catalog_count,
                    r.missing_in_class_count, r.conditional_stc_detected_count,
                    r.extended_postponed_detected_count, r.unmapped_low_confidence_count,
                    r.flags_json, r.notifications_sent_json, r.mapping_version_used,
                    r.anomaly_breaches_json
                FROM dbo.vims_certs_reconciliation_run r
                INNER JOIN dbo.vims_certs_class_status_snapshot s ON s.snapshot_id = r.snapshot_id
                LEFT JOIN dbo.VesselData v ON v.id = s.vessel_id
                {where_sql}
                ORDER BY s.printed_on_date DESC, r.ran_at DESC
                OFFSET {offset} ROWS FETCH NEXT {safe_page_size} ROWS ONLY
                """,
                params,
            )
            return {"count": count, "results": _fetch_all(cursor)}

    def get_run_detail(self, run_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    r.run_id, r.snapshot_id, s.vessel_id, v.vesselName AS vessel_name,
                    v.imoNumber AS imo_number, s.class_society, s.printed_on_date,
                    s.parse_status, s.parser_version, r.ran_at,
                    r.matches_count, r.mismatches_count, r.missing_in_catalog_count,
                    r.missing_in_class_count, r.conditional_stc_detected_count,
                    r.extended_postponed_detected_count, r.unmapped_low_confidence_count,
                    r.flags_json, r.notifications_sent_json, r.mapping_version_used,
                    r.anomaly_breaches_json
                FROM dbo.vims_certs_reconciliation_run r
                INNER JOIN dbo.vims_certs_class_status_snapshot s ON s.snapshot_id = r.snapshot_id
                LEFT JOIN dbo.VesselData v ON v.id = s.vessel_id
                WHERE r.run_id = %s
                """,
                [run_id],
            )
            run = _fetch_one(cursor)
            if run is None:
                return None
            cursor.execute(
                """
                SELECT
                    f.flag_id, f.run_id, f.bucket, f.catalog_id, c.display_name AS catalog_display_name,
                    f.tracked_item_id, f.class_row_extract_json, f.diff_json,
                    f.reviewed_by, f.reviewed_at, f.resolution_action, f.resolved_at
                FROM dbo.vims_certs_reconciliation_flag f
                LEFT JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = f.catalog_id
                WHERE f.run_id = %s
                ORDER BY
                    CASE f.bucket
                        WHEN 'mismatch' THEN 1
                        WHEN 'missing_in_catalog' THEN 2
                        WHEN 'missing_in_class' THEN 3
                        ELSE 4
                    END,
                    f.resolved_at,
                    f.flag_id
                """,
                [run_id],
            )
            return {"run": run, "flags": _fetch_all(cursor)}

    def get_flag_context(self, flag_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    f.flag_id, f.run_id, f.bucket, f.class_row_extract_json,
                    s.snapshot_id, s.vessel_id, s.class_society
                FROM dbo.vims_certs_reconciliation_flag f
                INNER JOIN dbo.vims_certs_reconciliation_run r ON r.run_id = f.run_id
                INNER JOIN dbo.vims_certs_class_status_snapshot s ON s.snapshot_id = r.snapshot_id
                WHERE f.flag_id = %s
                """,
                [flag_id],
            )
            return _fetch_one(cursor)

    def list_master_messages(
        self,
        *,
        vessel_id: str,
        include_reviewed: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        safe_page = max(int(page or 1), 1)
        safe_page_size = max(1, min(int(page_size or 50), 100))
        offset = (safe_page - 1) * safe_page_size
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                WITH messages AS (
                    {_master_message_select_sql()}
                    WHERE s.vessel_id = %s
                      AND f.resolution_action = N'notified_master'
                )
                SELECT COUNT(*)
                FROM messages
                WHERE (%s = 1 OR master_reviewed_at IS NULL)
                """,
                [vessel_id, int(include_reviewed)],
            )
            count = int(cursor.fetchone()[0] or 0)
            cursor.execute(
                f"""
                WITH messages AS (
                    {_master_message_select_sql()}
                    WHERE s.vessel_id = %s
                      AND f.resolution_action = N'notified_master'
                )
                SELECT *
                FROM messages
                WHERE (%s = 1 OR master_reviewed_at IS NULL)
                ORDER BY
                    CASE WHEN master_reviewed_at IS NULL THEN 0 ELSE 1 END,
                    COALESCE(office_notified_at, reviewed_at) DESC,
                    flag_id
                OFFSET {offset} ROWS FETCH NEXT {safe_page_size} ROWS ONLY
                """,
                [vessel_id, int(include_reviewed)],
            )
            return {"count": count, "results": _fetch_all(cursor)}

    def get_master_message(self, flag_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                {_master_message_select_sql()}
                WHERE f.flag_id = %s
                  AND f.resolution_action = N'notified_master'
                """,
                [flag_id],
            )
            return _fetch_one(cursor)

    def add_mapping_for_flag(
        self,
        flag_id: str,
        *,
        catalog_id: str,
        cert_or_survey_kind: str,
        notes: str | None,
        actor_id: str,
    ) -> dict[str, Any] | None:
        context = self.get_flag_context(flag_id)
        if context is None:
            return None
        if str(context.get("bucket") or "") not in MAPPING_ELIGIBLE_BUCKETS:
            raise ValueError("Only missing/unmapped reconciliation flags can add ClassCodeMapping rows.")
        class_row = _json_object(context.get("class_row_extract_json"))
        if not isinstance(class_row, dict):
            raise ValueError("Reconciliation flag does not contain a class row extract.")
        class_code = _class_code(class_row).strip()
        if not class_code:
            raise ValueError("Reconciliation flag does not contain a class code or name.")

        before_flag = self._get_flag(flag_id)
        class_society = str(context.get("class_society") or "").upper()
        previous_mapping = self._get_active_mapping(class_society=class_society, class_code_or_name=class_code)
        next_version = self._next_mapping_version(class_society=class_society, class_code_or_name=class_code)
        audit_action = "edit_class_mapping" if previous_mapping else "add_class_mapping"

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_class_code_mapping
                SET active = 0,
                    updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE class_society = %s
                  AND UPPER(LTRIM(RTRIM(class_code_or_name))) = UPPER(LTRIM(RTRIM(%s)))
                  AND active = 1
                """,
                [actor_id, class_society, class_code],
            )
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_class_code_mapping (
                    class_society, class_code_or_name, catalog_id, cert_or_survey_kind,
                    notes, version, active, created_by, updated_by
                )
                OUTPUT
                    inserted.mapping_id, inserted.class_society, inserted.class_code_or_name,
                    inserted.catalog_id, inserted.cert_or_survey_kind, inserted.notes,
                    inserted.version, inserted.active, inserted.created_at, inserted.created_by,
                    inserted.updated_at, inserted.updated_by
                VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s)
                """,
                [
                    class_society,
                    class_code,
                    catalog_id,
                    cert_or_survey_kind,
                    notes,
                    next_version,
                    actor_id,
                    actor_id,
                ],
            )
            new_mapping = _fetch_one(cursor)
            cursor.execute(
                """
                UPDATE dbo.vims_certs_reconciliation_flag
                SET reviewed_by = %s,
                    reviewed_at = SYSUTCDATETIME(),
                    resolution_action = %s,
                    resolved_at = SYSUTCDATETIME()
                WHERE flag_id = %s
                """,
                [actor_id, "mapping_added" if audit_action == "add_class_mapping" else "mapping_edited", flag_id],
            )

        snapshot = self._get_snapshot_for_reconciliation(str(context["snapshot_id"]))
        _, new_run = self.reconcile_snapshot(snapshot) if snapshot else (None, None)
        after_flag = self._get_flag(flag_id)
        return {
            "audit_action": audit_action,
            "before": previous_mapping,
            "after": new_mapping,
            "flag_before": before_flag,
            "flag_after": after_flag,
            "run": new_run,
            "context": context,
        }

    def review_flag(self, flag_id: str, *, actor_id: str, action: str) -> dict[str, Any] | None:
        before = self._get_flag(flag_id)
        if before is None:
            return None
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_reconciliation_flag
                SET reviewed_by = %s,
                    reviewed_at = SYSUTCDATETIME(),
                    resolution_action = %s,
                    resolved_at = SYSUTCDATETIME()
                WHERE flag_id = %s
                """,
                [actor_id, action, flag_id],
            )
        after = self._get_flag(flag_id)
        detail = self.get_run_detail(str(before["run_id"]))
        return {"before": before, "after": after, "run": detail["run"] if detail else None}

    def reconcile_snapshot(self, snapshot: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        parsed_payload = _json_object(snapshot.get("parsed_payload_json")) or {}
        mappings = self._list_mappings(str(snapshot.get("class_society") or ""))
        tracked_items = self._list_tracked_items(str(snapshot.get("vessel_id") or ""))
        result = build_reconciliation_flags(parsed_payload=parsed_payload, tracked_items=tracked_items, mappings=mappings)
        anomaly_breaches = evaluate_reconciliation_anomalies(
            counts=result.counts,
            parsed_payload=parsed_payload,
            tracked_items=tracked_items,
            snapshot=snapshot,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_reconciliation_run (
                    snapshot_id, matches_count, mismatches_count, missing_in_catalog_count,
                    missing_in_class_count, conditional_stc_detected_count,
                    extended_postponed_detected_count, unmapped_low_confidence_count,
                    flags_json, notifications_sent_json, mapping_version_used, anomaly_breaches_json
                )
                OUTPUT inserted.run_id
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(snapshot["snapshot_id"]),
                    result.counts["matches_count"],
                    result.counts["mismatches_count"],
                    result.counts["missing_in_catalog_count"],
                    result.counts["missing_in_class_count"],
                    result.counts["conditional_stc_detected_count"],
                    result.counts["extended_postponed_detected_count"],
                    result.counts["unmapped_low_confidence_count"],
                    json.dumps(result.flags, default=str),
                    "[]",
                    result.mapping_version_used,
                    json.dumps(anomaly_breaches, default=str),
                ],
            )
            run_id = str(cursor.fetchone()[0])
            for flag in result.flags:
                cursor.execute(
                    """
                    INSERT INTO dbo.vims_certs_reconciliation_flag (
                        run_id, bucket, catalog_id, tracked_item_id, class_row_extract_json, diff_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [
                        run_id,
                        flag["bucket"],
                        flag.get("catalog_id"),
                        flag.get("tracked_item_id"),
                        json.dumps(flag.get("class_row_extract"), default=str) if flag.get("class_row_extract") is not None else None,
                        json.dumps(flag.get("diff") or {}, default=str),
                    ],
                )
            cursor.execute(
                """
                UPDATE dbo.vims_certs_class_status_snapshot
                SET reconciliation_run_id = %s,
                    parse_status = %s,
                    parse_completed_at = COALESCE(parse_completed_at, SYSUTCDATETIME())
                WHERE snapshot_id = %s
                """,
                [run_id, "success", str(snapshot["snapshot_id"])],
            )
        detail = self.get_run_detail(run_id)
        if detail:
            notification_result = dispatch_parser_anomaly_notifications(
                run=detail["run"],
                anomaly_breaches=anomaly_breaches,
                flags=detail["flags"],
            )
            if notification_result.get("notificationsSent"):
                self._update_notifications_sent(run_id, notification_result["notificationsSent"])
                detail = self.get_run_detail(run_id) or detail
        return snapshot, detail["run"] if detail else {"run_id": run_id}

    def _get_flag(self, flag_id: str) -> dict[str, Any] | None:
        detail = self.get_flag_context(flag_id)
        if detail is None:
            return None
        run_detail = self.get_run_detail(str(detail["run_id"]))
        if run_detail is None:
            return None
        for flag in run_detail["flags"]:
            if str(flag.get("flag_id")) == str(flag_id):
                return flag
        return None

    def _list_mappings(self, class_society: str) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT class_code_or_name, catalog_id, version
                FROM dbo.vims_certs_class_code_mapping
                WHERE class_society = %s
                  AND active = 1
                """,
                [class_society.upper()],
            )
            return _fetch_all(cursor)

    def _get_active_mapping(self, *, class_society: str, class_code_or_name: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    mapping_id, class_society, class_code_or_name, catalog_id, cert_or_survey_kind,
                    notes, version, active, created_at, created_by, updated_at, updated_by
                FROM dbo.vims_certs_class_code_mapping
                WHERE class_society = %s
                  AND UPPER(LTRIM(RTRIM(class_code_or_name))) = UPPER(LTRIM(RTRIM(%s)))
                  AND active = 1
                ORDER BY version DESC
                """,
                [class_society.upper(), class_code_or_name],
            )
            return _fetch_one(cursor)

    def _next_mapping_version(self, *, class_society: str, class_code_or_name: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(version), 0)
                FROM dbo.vims_certs_class_code_mapping
                WHERE class_society = %s
                  AND UPPER(LTRIM(RTRIM(class_code_or_name))) = UPPER(LTRIM(RTRIM(%s)))
                """,
                [class_society.upper(), class_code_or_name],
            )
            row = cursor.fetchone()
        return int((row[0] if row else 0) or 0) + 1

    def _get_snapshot_for_reconciliation(self, snapshot_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    snapshot_id, vessel_id, class_society, parsed_payload_json,
                    parse_started_at, parse_completed_at
                FROM dbo.vims_certs_class_status_snapshot
                WHERE snapshot_id = %s
                """,
                [snapshot_id],
            )
            return _fetch_one(cursor)

    def _list_tracked_items(self, vessel_id: str) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    t.tracked_item_id, t.catalog_id, c.is_class_tracked AS catalog_is_class_tracked,
                    t.certificate_number, t.issue_date, t.expiry_date,
                    t.last_done_date, t.next_due_date, t.postponed_until
                FROM dbo.vims_certs_tracked_item t
                INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
                WHERE t.vessel_id = %s
                  AND t.lifecycle_status <> 'onboarding_quarantine'
                """,
                [vessel_id],
            )
            return _fetch_all(cursor)

    def _update_notifications_sent(self, run_id: str, notifications_sent: list[dict[str, Any]]) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_reconciliation_run
                SET notifications_sent_json = %s
                WHERE run_id = %s
                """,
                [json.dumps(notifications_sent, default=str), run_id],
            )


def _json_object(value: Any) -> dict[str, Any] | list[Any] | None:
    if not value:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, (dict, list)) else None


def _parser_anomaly_required_groups(anomaly_breaches: list[dict[str, Any]]) -> set[str]:
    groups = {"dpa"}
    for breach in anomaly_breaches:
        breach_type = str(breach.get("type") or "")
        if breach_type in {"mismatch_rate", "unmapped_rate", "unmapped_critical_rate"}:
            groups.add("marine_supt")
        elif breach_type in PARSER_HARD_ANOMALY_TYPES:
            groups.add("tech_supt")
        else:
            groups.add("dpa")
    return groups


def _parser_anomaly_role_group(role: str) -> str | None:
    key = _role_key(role)
    if key in DPA_ROLE_KEYS or "dpa" in key:
        return "dpa"
    if key in MARINE_SUPT_ROLE_KEYS:
        return "marine_supt"
    if key in TECH_SUPT_ROLE_KEYS:
        return "tech_supt"
    return None


def _load_default_office_recipients() -> list[CertNotificationRecipient]:
    if "users" not in connection.introspection.table_names():
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT employee_id, employee_role
            FROM {_qualified("users")}
            WHERE COALESCE(is_active, 1) = 1
              AND COALESCE(is_deleted, 0) = 0
              AND employee_role IS NOT NULL
            """
        )
        rows = cursor.fetchall()

    return [
        CertNotificationRecipient(user_id=str(employee_id), role=str(role), side="office")
        for employee_id, role in rows
        if employee_id and role
    ]


def _role_key(role: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(role or "").lower())


def _qualified(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name
