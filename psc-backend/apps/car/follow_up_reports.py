"""Helpers for attaching inspection follow-up report metadata to CAR exports."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from django.core import signing
from django.db import connection

from apps.accounts.models import HRM501, OfficeUser
from apps.car.models import ActivityHistory
from apps.inspection.deficiency_models import Deficiency, DeficiencyActionHistory
from apps.inspection.models import InspectionReport


FOLLOW_UP_REPORT_LINK_SALT = "apps.car.follow_up_report_link"
FOLLOW_UP_REPORT_LINK_MAX_AGE_SECONDS = 60 * 60
FOLLOW_UP_DEFICIENCY_MARKER_RE = re.compile(r"\s*\[CAR_DEFICIENCIES:([^\]]*)\]\s*$")
FOLLOW_UP_LEGACY_MATCH_WINDOW_SECONDS = 120
FOLLOW_UP_LEGACY_BATCH_TOLERANCE_SECONDS = 10


def _format_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _strip_deficiency_marker(description: Any) -> str:
    return FOLLOW_UP_DEFICIENCY_MARKER_RE.sub("", str(description or "")).strip()


def _normalize_id(value: Any) -> str:
    return str(value or "").replace("-", "").lower()


def _description_matches_deficiency(description: Any, deficiency_id: Any) -> bool | None:
    match = FOLLOW_UP_DEFICIENCY_MARKER_RE.search(str(description or ""))
    if not match:
        return None

    deficiency_ids = {
        _normalize_id(item.strip())
        for item in match.group(1).split(",")
        if item.strip()
    }
    return _normalize_id(deficiency_id) in deficiency_ids


def _legacy_report_matches_deficiency(
    *,
    uploaded_at: Any,
    deficiency_id: Any,
    inspection_history_rows: list[dict[str, Any]],
    inspection_deficiency_rows: list[dict[str, Any]],
) -> bool:
    if not uploaded_at:
        return False

    updated_same_day_ids = {
        _normalize_id(row.get("id"))
        for row in inspection_deficiency_rows
        if row.get("updated_date")
        and hasattr(row.get("updated_date"), "date")
        and hasattr(uploaded_at, "date")
        and row["updated_date"].date() == uploaded_at.date()
    }
    if len(updated_same_day_ids) == 1:
        return _normalize_id(deficiency_id) in updated_same_day_ids

    candidates: list[tuple[str, float]] = []
    for history in inspection_history_rows:
        changed_at = history.get("changed_at")
        if not changed_at:
            continue
        try:
            seconds = abs((uploaded_at - changed_at).total_seconds())
        except Exception:
            continue
        if seconds <= FOLLOW_UP_LEGACY_MATCH_WINDOW_SECONDS:
            candidates.append((_normalize_id(history.get("deficiency_id")), seconds))

    if not candidates:
        return False

    nearest_seconds = min(seconds for _, seconds in candidates)
    current_deficiency_id = _normalize_id(deficiency_id)
    closest_deficiency_ids = {
        candidate_deficiency_id
        for candidate_deficiency_id, seconds in candidates
        if seconds <= nearest_seconds + FOLLOW_UP_LEGACY_BATCH_TOLERANCE_SECONDS
    }
    if len(closest_deficiency_ids) != 1:
        return False

    return current_deficiency_id in closest_deficiency_ids


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except (TypeError, ValueError):
        return False


def _query_single_value(sql: str, params: list[Any]) -> str:
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
    except Exception:
        return ""
    return str(row[0]).strip() if row and row[0] else ""


def _resolve_vessel_user_display(raw_value: str) -> str:
    if _is_uuid(raw_value):
        display = _query_single_value(
            """
            SELECT TOP 1
                LTRIM(RTRIM(
                    CONCAT(
                        COALESCE(NULLIF(rank_name, ''), ''),
                        CASE WHEN COALESCE(NULLIF(rank_name, ''), '') <> '' THEN ' - ' ELSE '' END,
                        COALESCE(NULLIF(CONCAT(COALESCE(first_name, ''), ' ', COALESCE(surname, '')), ' '), CrewID)
                    )
                ))
            FROM HRM501
            WHERE id = CAST(%s AS uniqueidentifier)
              AND is_active = 1
              AND is_deleted = 0
            """,
            [raw_value],
        )
        if display:
            return display

    display = _query_single_value(
        """
        SELECT TOP 1
            LTRIM(RTRIM(
                CONCAT(
                    COALESCE(NULLIF(rank_name, ''), ''),
                    CASE WHEN COALESCE(NULLIF(rank_name, ''), '') <> '' THEN ' - ' ELSE '' END,
                    COALESCE(NULLIF(CONCAT(COALESCE(first_name, ''), ' ', COALESCE(surname, '')), ' '), CrewID)
                )
            ))
        FROM HRM501
        WHERE (LOWER(CrewID) = LOWER(%s) OR LOWER(user_id) = LOWER(%s))
          AND is_active = 1
          AND is_deleted = 0
        """,
        [raw_value, raw_value],
    )
    if display:
        return display

    crew_id = _query_single_value(
        """
        SELECT TOP 1 CrewID
        FROM Ship_UsersLogin
        WHERE (
            LOWER(CAST(id AS nvarchar(64))) = LOWER(%s)
            OR LOWER(CrewID) = LOWER(%s)
        )
          AND ISNULL(is_active, 1) = 1
          AND ISNULL(is_deleted, 0) = 0
        """,
        [raw_value, raw_value],
    )
    return crew_id


def _resolve_uploaded_by_display(uploaded_by: Any, *, fallback_name: str = "") -> str:
    raw_value = str(uploaded_by or "").strip()
    if not raw_value:
        return fallback_name

    if fallback_name and raw_value == fallback_name:
        return fallback_name

    if fallback_name and _is_uuid(raw_value):
        return fallback_name

    try:
        office_user = (
            OfficeUser.objects.filter(employee_id__iexact=raw_value).first()
            or OfficeUser.objects.filter(username__iexact=raw_value).first()
        )
        if office_user:
            return office_user.full_name
    except Exception:
        pass

    display = _resolve_vessel_user_display(raw_value)
    if display:
        return display

    return fallback_name or raw_value


def _latest_follow_up_activity(inspection_id: Any, deficiency_id: Any = None) -> dict[str, Any]:
    if deficiency_id:
        history = (
            DeficiencyActionHistory.objects.filter(
                deficiency_id=deficiency_id,
                deficiency__inspection_id=inspection_id,
            )
            .order_by("-changed_at")
            .first()
        )
        if not history:
            return {}
        return {
            "reinspection_date": "",
            "notes": history.change_reason or "",
            "recorded_by": history.changed_by or "",
            "recorded_at": _format_datetime(history.changed_at),
        }

    activity = (
        ActivityHistory.objects.filter(
            entity_type="INSPECTION",
            entity_id=inspection_id,
            event_type="PSC_FOLLOW_UP_RECORDED",
        )
        .order_by("-performed_at")
        .first()
    )
    if not activity:
        return {}

    description = str(activity.event_description or "")
    reinspection_match = re.search(r"Reinspection date:\s*([^\.]+)", description)
    notes_match = re.search(r"Notes:\s*(.+)$", description)
    return {
        "reinspection_date": reinspection_match.group(1).strip() if reinspection_match else "",
        "notes": notes_match.group(1).strip() if notes_match else "",
        "recorded_by": activity.performed_by_name or activity.performed_by or "",
        "recorded_at": _format_datetime(activity.performed_at),
    }


def _follow_up_action_updates(inspection_id: Any, deficiency_id: Any = None) -> list[dict[str, Any]]:
    if not inspection_id:
        return []

    filters = {"deficiency__inspection_id": inspection_id}
    if deficiency_id:
        filters["deficiency_id"] = deficiency_id

    histories = (
        DeficiencyActionHistory.objects.filter(**filters)
        .select_related("deficiency")
        .order_by("changed_at", "id")
    )
    updates: list[dict[str, Any]] = []
    for history in histories:
        deficiency = history.deficiency
        updates.append(
            {
                "deficiency_code": deficiency.def_code,
                "deficiency_description": deficiency.description,
                "from_action_code": history.previous_action_code,
                "to_action_code": history.new_action_code,
                "notes": history.change_reason,
                "changed_by": history.changed_by,
                "changed_at": _format_datetime(history.changed_at),
            }
        )
    return updates


def build_follow_up_report_token(report_id: Any, inspection_id: Any) -> str:
    return signing.dumps(
        {
            "report_id": str(report_id),
            "inspection_id": str(inspection_id),
        },
        salt=FOLLOW_UP_REPORT_LINK_SALT,
        compress=True,
    )


def build_follow_up_report_url(request: Any, *, report_id: Any, inspection_id: Any) -> str:
    query = urlencode(
        {
            "report_token": build_follow_up_report_token(report_id, inspection_id),
        }
    )
    return request.build_absolute_uri(
        f"/api/psc/inspections/reports/{report_id}/view/?{query}"
    )


def is_valid_follow_up_report_token(
    token: str | None,
    *,
    report_id: Any,
    inspection_id: Any,
    max_age: int = FOLLOW_UP_REPORT_LINK_MAX_AGE_SECONDS,
) -> bool:
    if not token:
        return False

    try:
        payload = signing.loads(
            token,
            salt=FOLLOW_UP_REPORT_LINK_SALT,
            max_age=max_age,
        )
    except signing.BadSignature:
        return False
    except signing.SignatureExpired:
        return False

    return (
        str(payload.get("report_id")) == str(report_id)
        and str(payload.get("inspection_id")) == str(inspection_id)
    )


def get_follow_up_reports_for_inspection(
    inspection_id: Any,
    request: Any = None,
    *,
    fallback_uploaded_by: str = "",
) -> list[dict[str, Any]]:
    """Return non-deleted follow-up report metadata for a parent PSC inspection."""
    if not inspection_id:
        return []

    rows = (
        InspectionReport.objects.filter(
            inspection_id=inspection_id,
            report_type="FOLLOW_UP",
            is_deleted=False,
        )
        .order_by("-uploaded_at")
        .values(
            "id",
            "file_name",
            "file_size",
            "mime_type",
            "description",
            "uploaded_by",
            "uploaded_at",
        )
    )

    return [
        {
            "id": str(row["id"]),
            "file_name": row["file_name"],
            "file_url": (
                build_follow_up_report_url(
                    request,
                    report_id=row["id"],
                    inspection_id=inspection_id,
                )
                if request
                else ""
            ),
            "file_size": row["file_size"],
            "mime_type": row["mime_type"],
            "description": _strip_deficiency_marker(row["description"]),
            "uploaded_by": _resolve_uploaded_by_display(
                row["uploaded_by"],
                fallback_name=fallback_uploaded_by,
            ),
            "uploaded_at": _format_datetime(row["uploaded_at"]),
        }
        for row in rows
    ]


def get_follow_up_reports_for_deficiency(
    *,
    inspection_id: Any,
    deficiency_id: Any,
    request: Any = None,
    fallback_uploaded_by: str = "",
) -> list[dict[str, Any]]:
    """Return follow-up report metadata linked to a specific CAR deficiency."""
    if not inspection_id or not deficiency_id:
        return []

    deficiency_history_times = list(
        DeficiencyActionHistory.objects.filter(
            deficiency_id=deficiency_id,
            deficiency__inspection_id=inspection_id,
        ).values_list("changed_at", flat=True)
    )
    if not deficiency_history_times:
        return []

    inspection_history_rows = list(
        DeficiencyActionHistory.objects.filter(
            deficiency__inspection_id=inspection_id,
        ).values("deficiency_id", "changed_at")
    )
    inspection_deficiency_rows = list(
        Deficiency.objects.filter(
            inspection_id=inspection_id,
            is_deleted=False,
        ).values("id", "updated_date")
    )

    has_follow_up_activity = bool(deficiency_history_times)
    if not has_follow_up_activity:
        return []

    rows = list(
        InspectionReport.objects.filter(
            inspection_id=inspection_id,
            report_type="FOLLOW_UP",
            is_deleted=False,
        )
        .order_by("-uploaded_at")
        .values(
            "id",
            "file_name",
            "file_size",
            "mime_type",
            "description",
            "uploaded_by",
            "uploaded_at",
        )
    )

    matched_rows = []
    for row in rows:
        marker_match = _description_matches_deficiency(row["description"], deficiency_id)
        if marker_match is True:
            matched_rows.append(row)
        elif marker_match is None and _legacy_report_matches_deficiency(
            uploaded_at=row["uploaded_at"],
            deficiency_id=deficiency_id,
            inspection_history_rows=inspection_history_rows,
            inspection_deficiency_rows=inspection_deficiency_rows,
        ):
            matched_rows.append(row)

    rows = matched_rows

    return [
        {
            "id": str(row["id"]),
            "file_name": row["file_name"],
            "file_url": (
                build_follow_up_report_url(
                    request,
                    report_id=row["id"],
                    inspection_id=inspection_id,
                )
                if request
                else ""
            ),
            "file_size": row["file_size"],
            "mime_type": row["mime_type"],
            "description": _strip_deficiency_marker(row["description"]),
            "uploaded_by": _resolve_uploaded_by_display(
                row["uploaded_by"],
                fallback_name=fallback_uploaded_by,
            ),
            "uploaded_at": _format_datetime(row["uploaded_at"]),
        }
        for row in rows
    ]

def attach_follow_up_reports(car_data: dict[str, Any], request: Any = None) -> dict[str, Any]:
    """Attach follow-up registration data for this CAR's own deficiency."""
    inspection = car_data.get("inspection") or {}
    deficiency = car_data.get("deficiency") or {}
    inspection_id = inspection.get("id")
    deficiency_id = deficiency.get("id")
    summary = _latest_follow_up_activity(inspection_id, deficiency_id)
    action_updates = _follow_up_action_updates(inspection_id, deficiency_id)
    car_data["follow_up_reports"] = get_follow_up_reports_for_deficiency(
        inspection_id=inspection_id,
        deficiency_id=deficiency_id,
        request=request,
        fallback_uploaded_by=str(summary.get("recorded_by") or ""),
    )
    car_data["follow_up_summary"] = summary if action_updates or car_data["follow_up_reports"] else {}
    car_data["follow_up_action_updates"] = action_updates
    return car_data
