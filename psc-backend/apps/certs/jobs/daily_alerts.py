from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import json
import re
from typing import Any, Iterable

from django.db import connection
from django.utils import timezone as django_timezone
from django.utils.dateparse import parse_date

from apps.certs.jobs.cadence_heartbeat import run_cadence_heartbeat
from apps.certs.services.alert_config_seed import default_alert_config_rows, seed_default_alert_configs
from apps.certs.services.notification_dispatcher import CertNotificationDispatcher, CertNotificationRecipient


EXPIRY_EVENTS: tuple[tuple[int, str], ...] = (
    (1, "cert_expiring_1d"),
    (7, "cert_expiring_7d"),
    (30, "cert_expiring_30d"),
    (90, "cert_expiring_90d"),
)
OFFICE_ROLE_ALIASES = {
    "dpa": {"dpa", "seqmanager", "designatedpersonashore", "designatedperson"},
    "marinesuperintendent": {"marinesuperintendent", "marinesupt", "marinesuptt"},
    "fleetmanager": {"fleetmanager", "fm"},
}
VESSEL_MASTER_ROLES = {"master", "captain", "actingmaster"}


@dataclass(frozen=True)
class DueCertAlert:
    trigger_event: str
    tracked_item_id: str
    vessel_id: str | None
    vessel_name: str
    certificate_name: str
    target_date: date | None
    days_to_go: int | None
    status: str


@dataclass(frozen=True)
class DailyCertAlertResult:
    dry_run: bool
    scanned: int
    due: int
    dispatched: int
    skipped_no_recipients: int
    skipped_already_sent: int
    max_alerts_reached: bool
    events: list[DueCertAlert]
    config_seeded: list[str]
    settings_seeded: bool
    heartbeat_stamped_at: datetime | None


def run_daily_cert_alerts(
    *,
    now: datetime | None = None,
    dispatcher: CertNotificationDispatcher | None = None,
    candidate_recipients: Iterable[CertNotificationRecipient] | None = None,
    apply: bool = False,
    include_pending_first_upload: bool = False,
    max_alerts: int = 100,
) -> DailyCertAlertResult:
    current = now or django_timezone.now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current_date = current.date()
    seed_result = None
    if apply:
        seed_result = seed_default_alert_configs(
            apply=True,
            actor_id="system.daily_certs_alerts",
            now=current,
        )
    config_map = _load_alert_config_map()

    rows = _load_candidate_rows()
    scanned = len(rows)
    events: list[DueCertAlert] = []
    dispatched = 0
    skipped_no_recipients = 0
    skipped_already_sent = 0
    max_alerts_reached = False
    notification_dispatcher = dispatcher or CertNotificationDispatcher()
    fixed_recipients = list(candidate_recipients) if candidate_recipients is not None else None
    heartbeat_stamped_at: datetime | None = None

    for row in rows:
        event = _classify_due_alert(
            row,
            current_date=current_date,
            config_map=config_map,
            include_pending_first_upload=include_pending_first_upload,
        )
        if event is None:
            continue
        if _alert_already_sent(event.tracked_item_id, event.trigger_event):
            skipped_already_sent += 1
            continue

        events.append(event)
        if len(events) > max_alerts:
            events.pop()
            max_alerts_reached = True
            break

        recipients = fixed_recipients if fixed_recipients is not None else _resolve_recipients(event, config_map)
        if not recipients:
            skipped_no_recipients += 1
            continue
        if not apply:
            continue

        dispatch_result = notification_dispatcher.dispatch(
            trigger_event=event.trigger_event,
            cert_row_id=event.tracked_item_id,
            vessel_id=event.vessel_id,
            recipients=recipients,
            title=_title_for_event(event),
            message=_message_for_event(event),
            payload=_payload_for_event(event),
            escalation_level=_escalation_level(event),
            idempotency_scope=event.trigger_event,
        )
        dispatched += len(dispatch_result.notification_rows)

    if apply:
        heartbeat_stamped_at = run_cadence_heartbeat(now=current).last_heartbeat_at

    return DailyCertAlertResult(
        dry_run=not apply,
        scanned=scanned,
        due=len(events),
        dispatched=dispatched,
        skipped_no_recipients=skipped_no_recipients,
        skipped_already_sent=skipped_already_sent,
        max_alerts_reached=max_alerts_reached,
        events=events,
        config_seeded=seed_result.created if seed_result else [],
        settings_seeded=bool(seed_result.settings_created) if seed_result else False,
        heartbeat_stamped_at=heartbeat_stamped_at,
    )


def _load_alert_config_map() -> dict[str, dict[str, Any]]:
    if _table_exists("vims_certs_alert_config"):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    trigger_event,
                    default_lead_days,
                    dpa_override_lead_days,
                    recipients_default_json,
                    dpa_override_recipients_json,
                    escalation_cadence_json
                FROM {_qualified("vims_certs_alert_config")}
                """
            )
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            if rows:
                return {str(row["trigger_event"]): row for row in rows}
    return {str(row["trigger_event"]): row for row in default_alert_config_rows()}


def _load_candidate_rows() -> list[dict[str, Any]]:
    required = {"vims_certs_tracked_item", "vims_certs_catalog_row"}
    if not required.issubset(set(connection.introspection.table_names())):
        return []

    vessel_join = ""
    vessel_select = "NULL AS vessel_name"
    if _table_exists("VesselData"):
        vessel_join = f"LEFT JOIN {_qualified('VesselData')} v ON v.id = t.vessel_id"
        vessel_select = "v.vesselName AS vessel_name"

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                t.tracked_item_id,
                t.vessel_id,
                t.status,
                t.expiry_date,
                t.window_open,
                t.window_close,
                t.pdf_missing,
                t.lifecycle_status,
                c.display_name,
                c.canonical_code,
                {vessel_select}
            FROM {_qualified("vims_certs_tracked_item")} t
            INNER JOIN {_qualified("vims_certs_catalog_row")} c
                ON c.catalog_id = t.catalog_id
            {vessel_join}
            WHERE COALESCE(t.lifecycle_status, %s) = %s
            ORDER BY t.expiry_date, t.window_close, c.display_name
            """,
            ["active", "active"],
        )
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _classify_due_alert(
    row: dict[str, Any],
    *,
    current_date: date,
    config_map: dict[str, dict[str, Any]],
    include_pending_first_upload: bool,
) -> DueCertAlert | None:
    tracked_item_id = str(row.get("tracked_item_id") or "")
    if not tracked_item_id:
        return None

    expiry_date = _as_date(row.get("expiry_date"))
    status = str(row.get("status") or "").strip().lower()
    if expiry_date is not None:
        days_to_expiry = (expiry_date - current_date).days
        if days_to_expiry < 0 and "cert_expired" in config_map:
            return _event_from_row(row, "cert_expired", expiry_date, days_to_expiry)
        for lead_days, trigger_event in EXPIRY_EVENTS:
            if trigger_event in config_map and 0 <= days_to_expiry <= lead_days:
                return _event_from_row(row, trigger_event, expiry_date, days_to_expiry)

    window_open = _as_date(row.get("window_open"))
    window_close = _as_date(row.get("window_close"))
    if window_open and window_close and window_open <= current_date <= window_close:
        days_to_close = (window_close - current_date).days
        if days_to_close <= _lead_days(config_map, "survey_window_closing", 30):
            return _event_from_row(row, "survey_window_closing", window_close, days_to_close)
        return _event_from_row(row, "survey_window_open", window_open, max((window_open - current_date).days, 0))

    if include_pending_first_upload and "pending_first_upload" in config_map:
        if status == "pending_first_upload" or _truthy(row.get("pdf_missing")):
            return _event_from_row(row, "pending_first_upload", None, None)

    return None


def _event_from_row(row: dict[str, Any], trigger_event: str, target_date: date | None, days_to_go: int | None) -> DueCertAlert:
    return DueCertAlert(
        trigger_event=trigger_event,
        tracked_item_id=str(row.get("tracked_item_id")),
        vessel_id=str(row.get("vessel_id")) if row.get("vessel_id") else None,
        vessel_name=str(row.get("vessel_name") or "Unknown vessel"),
        certificate_name=str(row.get("display_name") or row.get("canonical_code") or "Certificate"),
        target_date=target_date,
        days_to_go=days_to_go,
        status=str(row.get("status") or ""),
    )


def _alert_already_sent(tracked_item_id: str, trigger_event: str) -> bool:
    if not _table_exists("vims_certs_notification_meta"):
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {_qualified("vims_certs_notification_meta")}
            WHERE cert_row_id = %s
              AND trigger_event = %s
            """,
            [tracked_item_id, trigger_event],
        )
        return int(cursor.fetchone()[0] or 0) > 0


def _resolve_recipients(event: DueCertAlert, config_map: dict[str, dict[str, Any]]) -> list[CertNotificationRecipient]:
    config = config_map.get(event.trigger_event) or {}
    recipient_config = _json_loads(config.get("dpa_override_recipients_json")) or _json_loads(config.get("recipients_default_json")) or {}
    office_roles = _configured_values(recipient_config, "officeRoles", "office_roles")
    vessel_roles = _configured_values(recipient_config, "vesselRoles", "vessel_roles")
    office_users = _configured_users(recipient_config, "officeUsers", "office_users", side="office")
    vessel_users = _configured_users(recipient_config, "vesselUsers", "vessel_users", side="vessel")

    recipients: list[CertNotificationRecipient] = []
    recipients.extend(office_users)
    recipients.extend(vessel_users)
    recipients.extend(_load_office_role_recipients(office_roles or ["DPA", "Marine Superintendent"]))
    if event.vessel_id and any(_role_key(role) in VESSEL_MASTER_ROLES for role in (vessel_roles or ["MASTER"])):
        master = _load_vessel_master_recipient(event.vessel_id)
        if master is not None:
            recipients.append(master)
    return _dedupe_recipients(recipients)


def _load_office_role_recipients(role_names: Iterable[str]) -> list[CertNotificationRecipient]:
    if not _table_exists("users"):
        return []

    wanted_keys: set[str] = set()
    for role_name in role_names:
        key = _role_key(role_name)
        wanted_keys.add(key)
        wanted_keys.update(OFFICE_ROLE_ALIASES.get(key, set()))

    role_join = ""
    role_select = "NULL AS mapped_role"
    if _table_exists("mapping_role_user") and _table_exists("master_role"):
        role_join = f"""
        LEFT JOIN {_qualified("mapping_role_user")} mru
            ON (mru.userid = u.employee_id OR mru.userid = u.username)
           AND COALESCE(mru.is_active, 1) = 1
           AND COALESCE(mru.is_deleted, 0) = 0
        LEFT JOIN {_qualified("master_role")} mr
            ON mr.id = mru.role_id
           AND COALESCE(mr.is_active, 1) = 1
           AND COALESCE(mr.is_deleted, 0) = 0
        """
        role_select = "mr.role_name AS mapped_role"

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT DISTINCT
                u.employee_id,
                u.employee_role,
                {role_select}
            FROM {_qualified("users")} u
            {role_join}
            WHERE COALESCE(u.is_active, 1) = 1
              AND COALESCE(u.is_deleted, 0) = 0
            """
        )
        rows = cursor.fetchall()

    recipients: list[CertNotificationRecipient] = []
    for employee_id, employee_role, mapped_role in rows:
        candidate_roles = [str(value) for value in (mapped_role, employee_role) if value]
        matched_role = next((role for role in candidate_roles if _role_key(role) in wanted_keys), None)
        if employee_id and matched_role:
            recipients.append(CertNotificationRecipient(user_id=str(employee_id), role=matched_role, side="office"))
    return recipients


def _load_vessel_master_recipient(vessel_id: str) -> CertNotificationRecipient | None:
    required = {"Crew_Onboarding_History", "HRM501"}
    if not required.issubset(set(connection.introspection.table_names())):
        return None

    if connection.vendor == "microsoft":
        sql = f"""
            SELECT TOP 1
                coh.CrewID,
                COALESCE(r.rank_name, h.rank_name, 'MASTER') AS rank_name
            FROM {_qualified("Crew_Onboarding_History")} coh
            INNER JOIN {_qualified("HRM501")} h
                ON h.CrewID = coh.CrewID
               AND ISNULL(h.is_deleted, 0) = 0
               AND ISNULL(h.is_active, 1) = 1
            LEFT JOIN {_qualified("master_applied_rank")} r
                ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
               AND ISNULL(r.is_deleted, 0) = 0
               AND ISNULL(r.is_active, 1) = 1
            WHERE coh.Vessel = CAST(%s AS uniqueidentifier)
              AND coh.SignOffDate IS NULL
              AND ISNULL(coh.is_active, 1) = 1
              AND ISNULL(coh.is_deleted, 0) = 0
              AND UPPER(LTRIM(RTRIM(COALESCE(r.rank_name, h.rank_name, '')))) IN (N'MASTER', N'CAPTAIN', N'ACTING MASTER')
            ORDER BY coh.SignOnDate DESC
        """
    else:
        sql = f"""
            SELECT coh.CrewID, COALESCE(h.rank_name, 'MASTER') AS rank_name
            FROM {_qualified("Crew_Onboarding_History")} coh
            INNER JOIN {_qualified("HRM501")} h ON h.CrewID = coh.CrewID
            WHERE coh.Vessel = %s
              AND coh.SignOffDate IS NULL
              AND COALESCE(coh.is_active, 1) = 1
              AND COALESCE(coh.is_deleted, 0) = 0
              AND UPPER(TRIM(COALESCE(h.rank_name, ''))) IN ('MASTER', 'CAPTAIN', 'ACTING MASTER')
            ORDER BY coh.SignOnDate DESC
        """

    with connection.cursor() as cursor:
        cursor.execute(sql, [vessel_id])
        row = cursor.fetchone()

    if not row or not row[0]:
        return None
    return CertNotificationRecipient(user_id=str(row[0]), role=str(row[1] or "MASTER"), side="vessel")


def _configured_values(config: Any, *keys: str) -> list[str]:
    if isinstance(config, list):
        return [str(value) for value in config if isinstance(value, str)]
    if not isinstance(config, dict):
        return []
    values: list[str] = []
    for key in keys:
        raw = config.get(key)
        if isinstance(raw, list):
            values.extend(str(value) for value in raw if value)
        elif raw:
            values.append(str(raw))
    return values


def _configured_users(config: Any, *keys: str, side: str) -> list[CertNotificationRecipient]:
    if not isinstance(config, dict):
        return []
    users: list[CertNotificationRecipient] = []
    for key in keys:
        raw = config.get(key)
        if not isinstance(raw, list):
            continue
        for item in raw:
            if isinstance(item, dict):
                user_id = item.get("userId") or item.get("user_id") or item.get("id")
                role = item.get("role") or ("DPA" if side == "office" else "MASTER")
            else:
                user_id = item
                role = "DPA" if side == "office" else "MASTER"
            if user_id:
                users.append(CertNotificationRecipient(user_id=str(user_id), role=str(role), side=side))
    return users


def _dedupe_recipients(recipients: Iterable[CertNotificationRecipient]) -> list[CertNotificationRecipient]:
    deduped: list[CertNotificationRecipient] = []
    seen: set[tuple[str, str]] = set()
    for recipient in recipients:
        key = (recipient.user_id, recipient.normalized_side())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(recipient)
    return deduped


def _title_for_event(event: DueCertAlert) -> str:
    if event.trigger_event == "cert_expired":
        return "Certificate expired"
    if event.trigger_event.startswith("cert_expiring_"):
        return f"Certificate expires in {event.days_to_go} day{'s' if event.days_to_go != 1 else ''}"
    if event.trigger_event == "survey_window_closing":
        return "Survey window closing"
    if event.trigger_event == "survey_window_open":
        return "Survey window open"
    if event.trigger_event == "pending_first_upload":
        return "Certificate PDF missing"
    return "Certificate alert"


def _message_for_event(event: DueCertAlert) -> str:
    target = f" on {event.target_date.isoformat()}" if event.target_date else ""
    if event.trigger_event == "cert_expired":
        return f"{event.certificate_name} for {event.vessel_name} expired{target}."
    if event.trigger_event.startswith("cert_expiring_"):
        return f"{event.certificate_name} for {event.vessel_name} expires{target}."
    if event.trigger_event == "survey_window_closing":
        return f"{event.certificate_name} survey window for {event.vessel_name} closes{target}."
    if event.trigger_event == "survey_window_open":
        return f"{event.certificate_name} survey window for {event.vessel_name} is open."
    if event.trigger_event == "pending_first_upload":
        return f"{event.certificate_name} for {event.vessel_name} still needs the first certificate PDF upload."
    return f"{event.certificate_name} for {event.vessel_name} needs attention."


def _payload_for_event(event: DueCertAlert) -> dict[str, Any]:
    return {
        "trackedItemId": event.tracked_item_id,
        "vesselId": event.vessel_id,
        "vesselName": event.vessel_name,
        "certificateName": event.certificate_name,
        "targetDate": event.target_date.isoformat() if event.target_date else None,
        "daysToGo": event.days_to_go,
        "status": event.status,
    }


def _escalation_level(event: DueCertAlert) -> int:
    if event.trigger_event == "cert_expired":
        return 3
    if event.days_to_go is not None and event.days_to_go <= 1:
        return 2
    if event.days_to_go is not None and event.days_to_go <= 7:
        return 1
    return 0


def _lead_days(config_map: dict[str, dict[str, Any]], trigger_event: str, default: int) -> int:
    try:
        value = config_map.get(trigger_event, {}).get("dpa_override_lead_days")
        if value is None:
            value = config_map.get(trigger_event, {}).get("default_lead_days")
        return int(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return parse_date(str(value))


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _json_loads(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return None


def _role_key(role: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(role).lower())


def _table_exists(table_name: str) -> bool:
    return table_name in connection.introspection.table_names()


def _qualified(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name
