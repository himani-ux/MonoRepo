from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.utils import timezone

from apps.safety.repositories.base import BaseRepository


SOI_COMPLIANCE_LABEL = "SOI Compliance %"


class SOIComplianceCalculator:
    def __init__(
        self,
        *,
        repository: BaseRepository | None = None,
        now_func=timezone.now,
    ) -> None:
        self.repository = repository or BaseRepository()
        self.now_func = now_func

    def get_summary(self, vessel_id: str, *, at_date: date | datetime | None = None) -> dict[str, object]:
        current_at = self._coerce_datetime(at_date or self.now_func()) or timezone.now()
        rows = self.repository.execute_query(
            """
            SELECT
                area.area_id,
                area.area_name,
                area.section_12_flag,
                COALESCE(map.applicable, 1) AS applicable,
                map.last_inspected_at,
                map.due_at
            FROM master_soi_area AS area
            LEFT JOIN vims_safety_soi_vessel_area_map AS map
                ON map.area_id = area.area_id
               AND map.vessel_id = %s
            WHERE area.active = %s
            ORDER BY area.display_order ASC, area.area_id ASC
            """,
            [str(vessel_id), True],
        )

        applicable_rows = [row for row in rows if bool(row.get("applicable", True))]
        has_any_completed_cycle = any(self._coerce_datetime(row.get("last_inspected_at")) is not None for row in applicable_rows)
        area_payloads = [
            self._build_area_payload(row=row, current_at=current_at, has_any_completed_cycle=has_any_completed_cycle)
            for row in applicable_rows
        ]

        applicable_area_count = len(area_payloads)
        inspected_area_count = sum(1 for row in area_payloads if row["status"] in {"GREEN", "AMBER"})
        amber_area_count = sum(1 for row in area_payloads if row["status"] == "AMBER")
        overdue_area_count = sum(1 for row in area_payloads if row["status"] == "RED")

        if applicable_area_count == 0 or not has_any_completed_cycle:
            compliance_percent: int | None = None
            display_value = "N/A - awaiting first cycle"
            status = "NA"
        else:
            compliance_percent = int(round((inspected_area_count / applicable_area_count) * 100))
            display_value = f"{compliance_percent}%"
            if overdue_area_count:
                status = "RED"
            elif amber_area_count:
                status = "AMBER"
            else:
                status = "GREEN"

        return {
            "label": SOI_COMPLIANCE_LABEL,
            "vessel_id": str(vessel_id),
            "calculated_at": current_at.isoformat(),
            "status": status,
            "compliance_percent": compliance_percent,
            "display_value": display_value,
            "applicable_area_count": applicable_area_count,
            "inspected_area_count": inspected_area_count,
            "amber_area_count": amber_area_count,
            "overdue_area_count": overdue_area_count,
            "areas": area_payloads,
        }

    def list_overdue_areas(self, vessel_id: str, *, at_date: date | datetime | None = None) -> list[dict[str, object]]:
        summary = self.get_summary(vessel_id, at_date=at_date)
        overdue_rows = [row for row in summary["areas"] if row["status"] == "RED"]
        overdue_rows.sort(key=lambda row: (str(row["due_at"]), int(row["area_id"])))
        return [
            {
                "area_id": row["area_id"],
                "area_name": row["area_name"],
                "last_inspected_at": row["last_inspected_at"],
                "due_at": row["due_at"],
                "overdue_days": row["days_overdue"],
                "message": self._build_message(area_id=int(row["area_id"]), overdue_days=int(row["days_overdue"] or 1)),
            }
            for row in overdue_rows
        ]

    def _build_area_payload(
        self,
        *,
        row,
        current_at: datetime,
        has_any_completed_cycle: bool,
    ) -> dict[str, object]:
        area_id = self._coerce_int(row.get("area_id")) or 0
        last_inspected_at = self._coerce_datetime(row.get("last_inspected_at"))
        due_at = self._coerce_datetime(row.get("due_at"))
        if due_at is None and last_inspected_at is not None:
            due_at = last_inspected_at + timedelta(days=90)

        status = "NA"
        days_since_last_inspection = None
        days_until_due = None
        days_overdue = None

        if last_inspected_at is None:
            status = "NA" if not has_any_completed_cycle else "PENDING"
        else:
            days_since_last_inspection = max((current_at.date() - last_inspected_at.date()).days, 0)
            due_date = (due_at or (last_inspected_at + timedelta(days=90))).date()
            days_until_due = (due_date - current_at.date()).days
            if days_since_last_inspection >= 90:
                status = "RED"
                days_overdue = max((current_at.date() - due_date).days, 1)
                days_until_due = 0
            elif days_since_last_inspection >= 80:
                status = "AMBER"
            else:
                status = "GREEN"

        return {
            "area_id": area_id,
            "area_name": (row.get("area_name") or "").strip() or None,
            "section_12_flag": bool(row.get("section_12_flag")),
            "status": status,
            "last_inspected_at": self._serialize_datetime(last_inspected_at),
            "due_at": self._serialize_datetime(due_at),
            "days_since_last_inspection": days_since_last_inspection,
            "days_until_due": days_until_due,
            "days_overdue": days_overdue,
        }

    def _build_message(self, *, area_id: int, overdue_days: int) -> str:
        unit = "day" if overdue_days == 1 else "days"
        return f"Area {area_id} overdue by {overdue_days} {unit}"

    def _coerce_datetime(self, value) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(value, timezone.get_current_timezone())
            return value
        if isinstance(value, date):
            combined = datetime.combine(value, time.min)
            return timezone.make_aware(combined, timezone.get_current_timezone())
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return None
            try:
                parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
            except ValueError:
                try:
                    parsed_date = date.fromisoformat(normalized)
                except ValueError:
                    return None
                parsed = datetime.combine(parsed_date, time.min)
            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed
        return None

    def _serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value.isoformat()

    def _coerce_int(self, value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
