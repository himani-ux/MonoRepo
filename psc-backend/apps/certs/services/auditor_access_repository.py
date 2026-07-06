from __future__ import annotations

from typing import Any
import json

from django.db import connection
from django.utils import timezone


def _fetch_all(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_one(cursor) -> dict[str, Any] | None:
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def parse_scope(scope_value: Any) -> dict[str, list[str]]:
    if isinstance(scope_value, str):
        try:
            parsed = json.loads(scope_value)
        except (TypeError, ValueError):
            parsed = {}
    elif isinstance(scope_value, dict):
        parsed = scope_value
    else:
        parsed = {}

    return {
        "vesselIds": _string_list(parsed.get("vesselIds") or parsed.get("vessels")),
        "sections": _string_list(parsed.get("sections") or parsed.get("sectionIds")),
        "certIds": _string_list(parsed.get("certIds") or parsed.get("certificateIds") or parsed.get("customCertIds")),
    }


class AuditorAccessRepository:
    def list_grants(self) -> list[dict[str, Any]]:
        with connection.cursor() as cursor:
            cursor.execute(_grant_select_sql("ORDER BY granted_at DESC"))
            return _fetch_all(cursor)

    def get_grant(self, grant_id: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(_grant_select_sql("WHERE grant_id = %s"), [grant_id])
            return _fetch_one(cursor)

    def get_grant_by_signup_token_hash(self, signup_token_hash: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(_grant_select_sql("WHERE signup_token_hash = %s"), [signup_token_hash])
            return _fetch_one(cursor)

    def create_grant(
        self,
        *,
        auditor_name: str,
        auditor_email: str,
        scope: dict[str, Any],
        expiry_at,
        granted_by: str,
        signup_token_hash: str,
    ) -> dict[str, Any]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dbo.vims_certs_external_auditor_access (
                    auditor_name, auditor_email, scope_json, expiry_at, granted_by, signup_token_hash
                )
                OUTPUT inserted.grant_id
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    auditor_name,
                    auditor_email,
                    json.dumps(parse_scope(scope)),
                    expiry_at,
                    granted_by,
                    signup_token_hash,
                ],
            )
            grant_id = str(cursor.fetchone()[0])
        return self.get_grant(grant_id) or {}

    def update_expiry(
        self,
        grant_id: str,
        *,
        expiry_at,
        revoked_via_expiry_edit: bool,
    ) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_external_auditor_access
                SET expiry_at = %s,
                    revoked_via_expiry_edit = %s
                WHERE grant_id = %s
                """,
                [expiry_at, 1 if revoked_via_expiry_edit else 0, grant_id],
            )
        return self.get_grant(grant_id)

    def mark_signup_used(self, grant_id: str, *, token_secret_hash: str) -> dict[str, Any] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_external_auditor_access
                SET signup_token_used_at = SYSUTCDATETIME(),
                    token_secret_hash = %s
                WHERE grant_id = %s
                  AND signup_token_used_at IS NULL
                """,
                [token_secret_hash, grant_id],
            )
        return self.get_grant(grant_id)

    def touch_last_accessed(self, grant_id: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.vims_certs_external_auditor_access
                SET last_accessed_at = SYSUTCDATETIME()
                WHERE grant_id = %s
                """,
                [grant_id],
            )

    def list_scoped_vessels(self, scope: dict[str, Any]) -> list[dict[str, Any]]:
        vessel_ids = parse_scope(scope).get("vesselIds") or []
        if not vessel_ids:
            return []
        placeholders = ", ".join(["%s"] * len(vessel_ids))
        params = [*vessel_ids, *vessel_ids]
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    CAST(id AS NVARCHAR(64)) AS id,
                    CAST(imoNumber AS NVARCHAR(32)) AS imo,
                    vesselName AS name,
                    vesselCode AS code
                FROM dbo.VesselData
                WHERE CAST(id AS NVARCHAR(64)) IN ({placeholders})
                   OR CAST(imoNumber AS NVARCHAR(32)) IN ({placeholders})
                ORDER BY vesselName
                """,
                params,
            )
            return _fetch_all(cursor)

    def list_scoped_certs(self, scope: dict[str, Any], *, imo: str | None = None) -> list[dict[str, Any]]:
        where, params = _scoped_cert_where(scope)
        if imo:
            where.append("CAST(vd.imoNumber AS NVARCHAR(32)) = %s")
            params.append(str(imo))
        with connection.cursor() as cursor:
            cursor.execute(_cert_select_sql(f"WHERE {' AND '.join(where)} ORDER BY c.print_order, c.display_name"), params)
            return _fetch_all(cursor)

    def get_scoped_cert(self, scope: dict[str, Any], tracked_item_id: str) -> dict[str, Any] | None:
        where, params = _scoped_cert_where(scope)
        where.append("t.tracked_item_id = %s")
        params.append(str(tracked_item_id))
        with connection.cursor() as cursor:
            cursor.execute(_cert_select_sql(f"WHERE {' AND '.join(where)}"), params)
            return _fetch_one(cursor)


def _grant_select_sql(suffix: str = "") -> str:
    return f"""
        SELECT
            grant_id, auditor_name, auditor_email, scope_json, expiry_at, granted_by,
            granted_at, signup_token_hash, signup_token_used_at, token_secret_hash,
            last_accessed_at, revoked_via_expiry_edit
        FROM dbo.vims_certs_external_auditor_access
        {suffix}
    """


def _cert_select_sql(where_sql: str) -> str:
    return f"""
        SELECT
            t.tracked_item_id, t.vessel_id, t.catalog_id,
            c.canonical_code AS catalog_code,
            c.display_name AS catalog_display_name,
            c.short_name AS catalog_short_name,
            c.section_id AS catalog_section_id,
            s.section_code AS catalog_section_code,
            s.display_name AS catalog_section_name,
            c.print_order AS catalog_print_order,
            c.mandatory_for_all_vessels AS catalog_mandatory_for_all_vessels,
            c.is_class_tracked AS catalog_is_class_tracked,
            c.submission_scope AS catalog_submission_scope,
            t.type, t.validity_type, t.form_variant, t.cadence_months, t.cadence_custom_days,
            t.parent_id, t.relationship_type, t.supersedes_id,
            t.issue_date, t.expiry_date, t.anniversary_date,
            t.window_open, t.window_close, t.last_done_date, t.next_due_date, t.postponed_until,
            t.status, t.certificate_number, t.issuing_authority, t.place_of_issue,
            t.extension_authority, t.extension_letter_pdf_id, t.extension_reason,
            t.pdf_attachment_id, t.pdf_missing, t.source, t.last_class_sync_id,
            t.approval_state, t.submitted_by, t.submitted_at, t.approved_by, t.approved_at,
            t.rejection_reason, t.rejection_count, t.draft_expires_at, t.lifecycle_status,
            t.row_version, t.version, t.created_at, t.created_by, t.updated_at, t.updated_by,
            vd.vesselName AS vessel_name,
            CAST(vd.imoNumber AS NVARCHAR(32)) AS vessel_imo
        FROM dbo.vims_certs_tracked_item t
        INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
        INNER JOIN dbo.vims_certs_catalog_section s ON s.section_id = c.section_id
        INNER JOIN dbo.VesselData vd ON vd.id = t.vessel_id
        {where_sql}
    """


def _scoped_cert_where(scope: dict[str, Any]) -> tuple[list[str], list[Any]]:
    parsed = parse_scope(scope)
    where = ["t.lifecycle_status = 'active'"]
    params: list[Any] = []
    vessel_ids = parsed.get("vesselIds") or []
    sections = parsed.get("sections") or []
    cert_ids = parsed.get("certIds") or []

    if vessel_ids:
        placeholders = ", ".join(["%s"] * len(vessel_ids))
        where.append(f"(CAST(t.vessel_id AS NVARCHAR(64)) IN ({placeholders}) OR CAST(vd.imoNumber AS NVARCHAR(32)) IN ({placeholders}))")
        params.extend([*vessel_ids, *vessel_ids])
    else:
        where.append("1 = 0")

    if sections:
        section_clause = " OR ".join(["s.section_code = %s", "CAST(s.section_id AS NVARCHAR(16)) = %s"] * len(sections))
        where.append(f"({section_clause})")
        for section in sections:
            params.extend([section, section])

    if cert_ids:
        placeholders = ", ".join(["%s"] * len(cert_ids))
        where.append(f"CAST(t.tracked_item_id AS NVARCHAR(64)) IN ({placeholders})")
        params.extend(cert_ids)

    return where, params


def _string_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    try:
        return [str(item).strip() for item in value if str(item).strip()]
    except TypeError:
        text = str(value).strip()
        return [text] if text else []


def is_grant_expired(row: dict[str, Any]) -> bool:
    expiry_at = row.get("expiry_at")
    if expiry_at is None:
        return True
    now = timezone.now()
    if timezone.is_naive(expiry_at):
        now = now.replace(tzinfo=None)
    return expiry_at <= now
