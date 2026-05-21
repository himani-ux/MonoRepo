from __future__ import annotations

from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.safety.repositories.reporting_repo import ReportingRepository


class Mscmepc3PositionFetcher:
    AUTO_SOURCE = "AUTO_FROM_DAILY_REPORT"
    AWAITING_SOURCE = "AWAITING_DAILY_REPORT"
    MANUAL_SOURCE = "MANUAL"

    def __init__(self, *, reporting_repository: ReportingRepository | None = None) -> None:
        self.reporting_repository = reporting_repository or ReportingRepository()

    def fetch_position(self, vessel_id: str, timestamp) -> dict[str, object]:
        occurred_at = self._coerce_datetime(timestamp)
        if not vessel_id or occurred_at is None:
            return self._awaiting_result()

        candidates = self.reporting_repository.find_position_candidates(
            vessel_id=str(vessel_id),
            occurred_at=occurred_at,
        )

        normalized_candidates: list[dict[str, object]] = []
        for row in candidates:
            normalized = self._normalize_candidate(row, occurred_at)
            if normalized is not None:
                normalized_candidates.append(normalized)

        if not normalized_candidates:
            return self._awaiting_result()

        normalized_candidates.sort(
            key=lambda row: (
                int(row["delta_minutes"]),
                int(row["source_priority"]),
            )
        )
        best = normalized_candidates[0]
        return {
            "awaiting_daily_report_match": False,
            "delta_minutes": best["delta_minutes"],
            "latitude": best["latitude"],
            "longitude": best["longitude"],
            "matched": True,
            "message": (
                f"Position auto-filled from Daily Report {best['source_reference']}. "
                "Edit if a more recent position is available."
            ),
            "position_daily_report_id": best["source_reference"],
            "position_source": self.AUTO_SOURCE,
            "report_date": best["report_date"].isoformat(),
            "source_reference": best["source_reference"],
            "source_table": best["source_table"],
        }

    def enrich_payload(self, payload: dict[str, object]) -> dict[str, object]:
        vessel_id = payload.get("vessel_id")
        occurred_at = payload.get("occurred_at")
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")
        position_source = payload.get("position_source")
        position_daily_report_id = payload.get("position_daily_report_id")

        has_manual_position = latitude not in (None, "") and longitude not in (None, "")
        if has_manual_position:
            if position_source in (None, ""):
                payload["position_source"] = self.MANUAL_SOURCE
            if position_daily_report_id:
                payload["awaiting_daily_report_match"] = False
                return payload

            result = self.fetch_position(vessel_id=str(vessel_id), timestamp=occurred_at)
            payload["awaiting_daily_report_match"] = bool(result["awaiting_daily_report_match"])
            return payload

        result = self.fetch_position(vessel_id=str(vessel_id), timestamp=occurred_at)
        if result["matched"]:
            payload["latitude"] = Decimal(str(result["latitude"]))
            payload["longitude"] = Decimal(str(result["longitude"]))
            payload["position_source"] = result["position_source"]
            payload["position_daily_report_id"] = result["position_daily_report_id"]
            payload["awaiting_daily_report_match"] = False
        elif vessel_id not in (None, "") and occurred_at is not None:
            payload["awaiting_daily_report_match"] = True
            payload.setdefault("position_source", self.AWAITING_SOURCE)

        return payload

    def _normalize_candidate(self, row: dict[str, object], occurred_at: datetime) -> dict[str, object] | None:
        report_date = self._coerce_datetime(row.get("report_date"))
        if report_date is None:
            return None

        latitude = self._to_signed_decimal(row.get("lat_deg"), row.get("lat_min"), row.get("lat_hemi"))
        longitude = self._to_signed_decimal(row.get("lon_deg"), row.get("lon_min"), row.get("lon_hemi"))
        if latitude is None or longitude is None:
            return None

        delta_minutes = abs(int((report_date - occurred_at).total_seconds() // 60))
        source_reference = self._build_source_reference(row)

        return {
            "delta_minutes": delta_minutes,
            "latitude": latitude,
            "longitude": longitude,
            "report_date": report_date,
            "source_priority": row.get("source_priority", 99),
            "source_reference": source_reference,
            "source_table": row.get("source_table"),
        }

    def _awaiting_result(self) -> dict[str, object]:
        return {
            "awaiting_daily_report_match": True,
            "delta_minutes": None,
            "latitude": None,
            "longitude": None,
            "matched": False,
            "message": (
                "No Daily Report within ±12h window; enter position manually. "
                "Record flagged awaiting_daily_report_match for DPA review."
            ),
            "position_daily_report_id": None,
            "position_source": self.AWAITING_SOURCE,
            "report_date": None,
            "source_reference": None,
            "source_table": None,
        }

    def _build_source_reference(self, row: dict[str, object]) -> str:
        source_table = row.get("source_table") or "DailyReport"
        auto_id = row.get("source_auto_id")
        source_id = row.get("source_id")
        identifier = auto_id if auto_id not in (None, "") else source_id
        return f"{source_table}:{identifier}"

    def _coerce_datetime(self, value) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            result = value
        else:
            parsed = parse_datetime(str(value))
            if parsed is None:
                return None
            result = parsed

        if timezone.is_naive(result):
            return result.replace(tzinfo=datetime_timezone.utc)
        return result.astimezone(datetime_timezone.utc)

    def _to_signed_decimal(self, degrees, minutes, hemisphere) -> float | None:
        if degrees in (None, "") or minutes in (None, "") or hemisphere in (None, ""):
            return None

        try:
            value = abs(float(degrees)) + (abs(float(minutes)) / 60.0)
        except (TypeError, ValueError):
            return None

        direction = str(hemisphere).strip().upper()
        if direction in {"S", "W"}:
            value *= -1
        return round(value, 6)

