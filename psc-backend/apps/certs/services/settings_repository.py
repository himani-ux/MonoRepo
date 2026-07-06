from __future__ import annotations

from decimal import Decimal
import json
import uuid
from typing import Any

from django.db import connection


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def _json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str, separators=(",", ":"))


def _decimal_param(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class SettingsRepository:
    def get_settings_snapshot(self) -> dict[str, Any]:
        return {
            "settings": self.get_settings_row(),
            "alert_configs": self.list_alert_configs(),
            "slack_routes": self.list_slack_routes(),
        }

    def get_settings_row(self) -> dict[str, Any] | None:
        sql = (
            """
            SELECT TOP 1 settings_id, singleton_key, last_heartbeat_at, created_at, updated_at, updated_by
            FROM dbo.vims_certs_settings
            WHERE singleton_key = 'certs'
            """
            if connection.vendor == "microsoft"
            else """
            SELECT settings_id, singleton_key, last_heartbeat_at, created_at, updated_at, updated_by
            FROM dbo.vims_certs_settings
            WHERE singleton_key = 'certs'
            LIMIT 1
            """
        )
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return _fetch_one(cursor)

    def list_alert_configs(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
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
                FROM dbo.vims_certs_alert_config
                ORDER BY trigger_event
                """
            )
            return _fetch_all(cursor)

    def list_slack_routes(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    vc.vessel_id,
                    v.vessel_name,
                    v.imo_number,
                    vc.slack_channel_vessel,
                    vc.slack_channel_office_default,
                    vc.updated_at,
                    vc.updated_by
                FROM dbo.vims_certs_vessel_config vc
                LEFT JOIN dbo.VesselData v ON v.id = vc.vessel_id
                WHERE vc.lifecycle_status <> 'decommissioned'
                ORDER BY v.vessel_name, vc.vessel_id
                """
            )
            return _fetch_all(cursor)

    def update_settings(self, values: dict[str, Any], *, actor_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        before = self.get_settings_snapshot()
        with connection.cursor() as cursor:
            for config in values.get("alertConfigs") or []:
                self._update_alert_config(cursor, config, actor_id=actor_id)

            retention_override = values.get("retentionOverride")
            if retention_override:
                self._update_retention_override(cursor, retention_override)

            for route in values.get("slackRoutes") or []:
                self._update_slack_route(cursor, route, actor_id=actor_id)

            cursor.execute(
                """
                UPDATE dbo.vims_certs_settings
                SET updated_at = SYSUTCDATETIME(),
                    updated_by = %s
                WHERE singleton_key = 'certs'
                """,
                [actor_id],
            )
            if int(getattr(cursor, "rowcount", 0) or 0) == 0:
                cursor.execute(
                    """
                    INSERT INTO dbo.vims_certs_settings (
                        settings_id, singleton_key, created_at, updated_at, updated_by
                    )
                    VALUES (%s, 'certs', SYSUTCDATETIME(), SYSUTCDATETIME(), %s)
                    """,
                    [str(uuid.uuid4()), actor_id],
                )
        after = self.get_settings_snapshot()
        return before, after

    def _update_alert_config(self, cursor, config: dict[str, Any], *, actor_id: str) -> None:
        cursor.execute(
            """
            UPDATE dbo.vims_certs_alert_config
            SET dpa_override_lead_days = %s,
                dpa_override_recipients_json = %s,
                escalation_cadence_json = %s,
                ocr_threshold_office = %s,
                ocr_threshold_vessel = %s,
                ocr_threshold_manual_floor = %s,
                class_snapshot_cadence_months = %s,
                class_snapshot_lead_months = %s,
                event_snapshot_grace_days = %s,
                draft_expire_days = %s,
                updated_at = SYSUTCDATETIME(),
                updated_by = %s
            WHERE config_id = %s
            """,
            [
                config.get("dpaOverrideLeadDays"),
                _json_dumps(config.get("dpaOverrideRecipients")),
                _json_dumps(config.get("escalationCadence")),
                _decimal_param(config.get("ocrThresholdOffice")),
                _decimal_param(config.get("ocrThresholdVessel")),
                _decimal_param(config.get("ocrThresholdManualFloor")),
                config.get("classSnapshotCadenceMonths"),
                config.get("classSnapshotLeadMonths"),
                config.get("eventSnapshotGraceDays"),
                config.get("draftExpireDays"),
                actor_id,
                str(config.get("id")),
            ],
        )

    def _update_retention_override(self, cursor, override: dict[str, Any]) -> None:
        cursor.execute(
            """
            UPDATE dbo.vims_certs_pdf_blob
            SET dpa_retention_override_until = %s
            WHERE blob_id = %s
            """,
            [override.get("dpaRetentionOverrideUntil"), str(override.get("blobId"))],
        )

    def _update_slack_route(self, cursor, route: dict[str, Any], *, actor_id: str) -> None:
        cursor.execute(
            """
            UPDATE dbo.vims_certs_vessel_config
            SET slack_channel_vessel = %s,
                slack_channel_office_default = %s,
                updated_at = SYSUTCDATETIME(),
                updated_by = %s
            WHERE vessel_id = %s
            """,
            [
                route.get("slackChannelVessel") or None,
                route.get("slackChannelOfficeDefault") or None,
                actor_id,
                str(route.get("vesselId")),
            ],
        )
