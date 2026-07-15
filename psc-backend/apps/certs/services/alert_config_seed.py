from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json
import uuid
from typing import Any

from django.db import connection, transaction
from django.utils import timezone


DEFAULT_RECIPIENTS = {
    "officeRoles": ["DPA", "Marine Superintendent"],
    "vesselRoles": ["MASTER"],
}
ESCALATION_CADENCE = {
    "repeatAfterDays": 1,
    "thresholds": ["90d", "30d", "7d", "1d", "expired"],
}


@dataclass(frozen=True)
class DefaultAlertConfig:
    trigger_event: str
    default_lead_days: int
    recipients_default: dict[str, Any]
    escalation_cadence: dict[str, Any]


@dataclass(frozen=True)
class AlertConfigSeedResult:
    created: list[str]
    existing: list[str]
    settings_created: bool
    dry_run: bool


DEFAULT_ALERT_CONFIGS: tuple[DefaultAlertConfig, ...] = (
    DefaultAlertConfig("cert_expiring_90d", 90, DEFAULT_RECIPIENTS, ESCALATION_CADENCE),
    DefaultAlertConfig("cert_expiring_30d", 30, DEFAULT_RECIPIENTS, ESCALATION_CADENCE),
    DefaultAlertConfig("cert_expiring_7d", 7, DEFAULT_RECIPIENTS, ESCALATION_CADENCE),
    DefaultAlertConfig("cert_expiring_1d", 1, DEFAULT_RECIPIENTS, ESCALATION_CADENCE),
    DefaultAlertConfig(
        "cert_expired",
        0,
        {"officeRoles": ["DPA", "Marine Superintendent", "Fleet Manager"], "vesselRoles": ["MASTER"]},
        ESCALATION_CADENCE,
    ),
    DefaultAlertConfig("survey_window_open", 0, DEFAULT_RECIPIENTS, ESCALATION_CADENCE),
    DefaultAlertConfig("survey_window_closing", 30, DEFAULT_RECIPIENTS, ESCALATION_CADENCE),
    DefaultAlertConfig(
        "pending_first_upload",
        0,
        {"officeRoles": ["DPA"], "vesselRoles": ["MASTER"]},
        {"repeatAfterDays": 7, "thresholds": ["first-upload-missing"]},
    ),
    DefaultAlertConfig(
        "class_snapshot_due",
        30,
        {"officeRoles": ["DPA", "Marine Superintendent"]},
        {"repeatAfterDays": 30, "thresholds": ["snapshot-due"]},
    ),
)


def seed_default_alert_configs(
    *,
    apply: bool = False,
    actor_id: str = "seed_certs_alert_config",
    now: datetime | None = None,
) -> AlertConfigSeedResult:
    alert_config_table_exists = _table_exists("vims_certs_alert_config")
    settings_table_exists = _table_exists("vims_certs_settings")
    existing = _existing_trigger_events()
    missing = [
        config for config in DEFAULT_ALERT_CONFIGS if alert_config_table_exists and config.trigger_event not in existing
    ]
    settings_exists = _settings_exists()
    created = [config.trigger_event for config in missing]
    settings_would_be_created = settings_table_exists and not settings_exists

    if not apply:
        return AlertConfigSeedResult(
            created=created,
            existing=sorted(existing),
            settings_created=settings_would_be_created,
            dry_run=True,
        )

    current = now or timezone.now()
    with transaction.atomic():
        for config in missing:
            _insert_alert_config(config, actor_id=actor_id, now=current)
        settings_created = _ensure_settings_row(actor_id=actor_id, now=current)

    return AlertConfigSeedResult(
        created=created,
        existing=sorted(existing | set(created)),
        settings_created=settings_created,
        dry_run=False,
    )


def default_alert_config_rows() -> list[dict[str, Any]]:
    return [
        {
            "config_id": None,
            "trigger_event": config.trigger_event,
            "default_lead_days": config.default_lead_days,
            "dpa_override_lead_days": None,
            "recipients_default_json": json.dumps(config.recipients_default, separators=(",", ":")),
            "dpa_override_recipients_json": None,
            "escalation_cadence_json": json.dumps(config.escalation_cadence, separators=(",", ":")),
        }
        for config in DEFAULT_ALERT_CONFIGS
    ]


def _existing_trigger_events() -> set[str]:
    if not _table_exists("vims_certs_alert_config"):
        return set()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT trigger_event FROM {_qualified('vims_certs_alert_config')}")
        return {str(row[0]) for row in cursor.fetchall() if row and row[0]}


def _settings_exists() -> bool:
    if not _table_exists("vims_certs_settings"):
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM {_qualified('vims_certs_settings')} WHERE singleton_key = %s",
            ["certs"],
        )
        return int(cursor.fetchone()[0] or 0) > 0


def _insert_alert_config(config: DefaultAlertConfig, *, actor_id: str, now: datetime) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {_qualified("vims_certs_alert_config")} (
                config_id,
                trigger_event,
                default_lead_days,
                dpa_override_lead_days,
                recipients_default_json,
                dpa_override_recipients_json,
                escalation_cadence_json,
                ocr_threshold_office,
                ocr_threshold_vessel,
                ocr_threshold_manual_floor,
                class_snapshot_cadence_months,
                class_snapshot_lead_months,
                event_snapshot_grace_days,
                draft_expire_days,
                created_at,
                updated_at,
                updated_by
            )
            VALUES (%s, %s, %s, NULL, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                str(uuid.uuid4()),
                config.trigger_event,
                config.default_lead_days,
                json.dumps(config.recipients_default, separators=(",", ":")),
                json.dumps(config.escalation_cadence, separators=(",", ":")),
                Decimal("0.800"),
                Decimal("0.850"),
                Decimal("0.600"),
                3,
                1,
                14,
                7,
                now,
                now,
                actor_id,
            ],
        )


def _ensure_settings_row(*, actor_id: str, now: datetime) -> bool:
    if not _table_exists("vims_certs_settings"):
        return False
    if _settings_exists():
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {_qualified("vims_certs_settings")} (
                settings_id, singleton_key, created_at, updated_at, updated_by
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            [str(uuid.uuid4()), "certs", now, now, actor_id],
        )
    return True


def _table_exists(table_name: str) -> bool:
    return table_name in connection.introspection.table_names()


def _qualified(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name
