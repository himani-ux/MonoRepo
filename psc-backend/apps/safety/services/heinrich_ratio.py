from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Q
from django.utils import timezone

from apps.safety.models import Incident, SOIFinding, SOIInspection


class HeinrichRatioService:
    WINDOW_DAYS = 365 * 3
    CONFIDENCE_WINDOW_DAYS = 365
    BENCHMARK = (
        ("major_injury", "Fatality / major injury", 1),
        ("minor_injury", "Minor injury", 10),
        ("property_damage", "Property damage", 30),
        ("near_miss", "Near miss", 600),
        ("hazards_observations", "Hazards / observations", 600),
    )

    def __init__(
        self,
        *,
        incident_model=Incident,
        finding_model=SOIFinding,
        inspection_model=SOIInspection,
        now_func=timezone.now,
    ) -> None:
        self.incident_model = incident_model
        self.finding_model = finding_model
        self.inspection_model = inspection_model
        self.now_func = now_func

    def build_panel(self, *, vessel_id: str | None = None, as_of=None) -> dict[str, object]:
        current_at = as_of or self.now_func()
        window_end = current_at.date()
        window_start = window_end - timedelta(days=self.WINDOW_DAYS - 1)
        confidence_window_start = window_end - timedelta(days=self.CONFIDENCE_WINDOW_DAYS - 1)

        incident_buckets = self._bucket_incidents(
            vessel_id=vessel_id,
            window_start=window_start,
            window_end=window_end,
        )
        near_miss_count = self._count_near_misses(
            vessel_id=vessel_id,
            window_start=window_start,
            window_end=window_end,
        )
        hazard_count = self._count_hazards(
            vessel_id=vessel_id,
            window_start=window_start,
            window_end=window_end,
        )

        layers = []
        for key, label, benchmark in self.BENCHMARK:
            actual = {
                "major_injury": incident_buckets["major_injury"],
                "minor_injury": incident_buckets["minor_injury"],
                "property_damage": incident_buckets["property_damage"],
                "near_miss": near_miss_count,
                "hazards_observations": hazard_count,
            }[key]
            variance = actual - benchmark
            layers.append(
                {
                    "actual": actual,
                    "benchmark": benchmark,
                    "key": key,
                    "label": label,
                    "variance": variance,
                }
            )

        confidence = self._build_confidence(
            vessel_id=vessel_id,
            window_start=confidence_window_start,
            window_end=window_end,
        )
        gap = self._build_reporting_culture_gap(
            major_injury=incident_buckets["major_injury"],
            minor_injury=incident_buckets["minor_injury"],
            property_damage=incident_buckets["property_damage"],
            near_miss=near_miss_count,
            hazards_observations=hazard_count,
        )

        return {
            "confidence": confidence,
            "layers": layers,
            "reporting_culture_gap": gap,
            "scope_id": vessel_id or "",
            "scope_type": "VESSEL" if vessel_id else "FLEET",
            "window_end": window_end.isoformat(),
            "window_start": window_start.isoformat(),
        }

    def _bucket_incidents(
        self,
        *,
        vessel_id: str | None,
        window_start: date,
        window_end: date,
    ) -> dict[str, int]:
        counts = {
            "major_injury": 0,
            "minor_injury": 0,
            "property_damage": 0,
        }
        queryset = self._base_incident_queryset(
            record_type=self.incident_model.RecordType.INCIDENT,
            vessel_id=vessel_id,
            window_start=window_start,
            window_end=window_end,
        )

        # The handover workspace does not yet carry a richer harm taxonomy column for the
        # Heinrich layers, so the panel uses the proven severity fields already locked in
        # the incident shell to keep the pyramid deterministic and reviewable.
        for incident in queryset.values("imo_classifier", "risk_band"):
            imo_classifier = incident["imo_classifier"]
            risk_band = incident["risk_band"]
            if imo_classifier == self.incident_model.ImoClassifier.SMC or risk_band == self.incident_model.RiskBand.RED:
                counts["major_injury"] += 1
            elif imo_classifier == self.incident_model.ImoClassifier.MC or risk_band == self.incident_model.RiskBand.YELLOW:
                counts["minor_injury"] += 1
            else:
                counts["property_damage"] += 1

        return counts

    def _count_near_misses(
        self,
        *,
        vessel_id: str | None,
        window_start: date,
        window_end: date,
    ) -> int:
        return self._base_incident_queryset(
            record_type=self.incident_model.RecordType.NEAR_MISS,
            vessel_id=vessel_id,
            window_start=window_start,
            window_end=window_end,
        ).count()

    def _count_hazards(
        self,
        *,
        vessel_id: str | None,
        window_start: date,
        window_end: date,
    ) -> int:
        queryset = self.finding_model.objects.filter(
            is_deleted=False,
            created_date__date__gte=window_start,
            created_date__date__lte=window_end,
        )
        if vessel_id:
            inspection_ids = self.inspection_model.objects.filter(
                is_deleted=False,
                vessel_id=vessel_id,
            ).values_list("id", flat=True)
            queryset = queryset.filter(inspection_id__in=inspection_ids)
        return queryset.count()

    def _build_confidence(
        self,
        *,
        vessel_id: str | None,
        window_start: date,
        window_end: date,
    ) -> dict[str, object]:
        incident_count = self._base_incident_queryset(
            record_type=self.incident_model.RecordType.INCIDENT,
            vessel_id=vessel_id,
            window_start=window_start,
            window_end=window_end,
        ).count()
        near_miss_count = self._base_incident_queryset(
            record_type=self.incident_model.RecordType.NEAR_MISS,
            vessel_id=vessel_id,
            window_start=window_start,
            window_end=window_end,
        ).count()

        if incident_count == 0 and near_miss_count == 0:
            return {
                "incident_count_12m": incident_count,
                "near_miss_count_12m": near_miss_count,
                "reason": "Insufficient data",
                "status": "RED",
                "tooltip": "Insufficient data for the rolling 12-month confidence check.",
            }
        if incident_count >= 5 and near_miss_count >= 20:
            return {
                "incident_count_12m": incident_count,
                "near_miss_count_12m": near_miss_count,
                "reason": "Stable sample size",
                "status": "GREEN",
                "tooltip": "Rolling 12-month sample meets the docsuite confidence threshold.",
            }
        return {
            "incident_count_12m": incident_count,
            "near_miss_count_12m": near_miss_count,
            "reason": "Below the confidence threshold",
            "status": "AMBER",
            "tooltip": "Rolling 12-month counts are below the >=5 incidents and >=20 near-miss benchmark.",
        }

    @staticmethod
    def _build_reporting_culture_gap(
        *,
        major_injury: int,
        minor_injury: int,
        property_damage: int,
        near_miss: int,
        hazards_observations: int,
    ) -> dict[str, object]:
        missing_layers: list[str] = []
        if major_injury > 0:
            if minor_injury == 0:
                missing_layers.append("minor injuries")
            if property_damage == 0:
                missing_layers.append("property damage")
        if (major_injury > 0 or minor_injury > 0) and near_miss == 0:
            missing_layers.append("near misses")
        if (major_injury > 0 or minor_injury > 0 or property_damage > 0) and hazards_observations == 0:
            missing_layers.append("hazards / observations")

        if not missing_layers:
            return {
                "is_gap": False,
                "message": "Reporting layers are present below the recorded incident severity.",
            }

        normalized = ", ".join(dict.fromkeys(missing_layers))
        return {
            "is_gap": True,
            "message": f"Reporting Culture Gap - missing lower-layer coverage for {normalized}.",
        }

    def _base_incident_queryset(
        self,
        *,
        record_type: str,
        vessel_id: str | None,
        window_start: date,
        window_end: date,
    ):
        queryset = self.incident_model.objects.filter(
            record_type=record_type,
            is_deleted=False,
            superseded_by_id__isnull=True,
        ).filter(
            Q(
                occurred_at__date__gte=window_start,
                occurred_at__date__lte=window_end,
            )
            | Q(
                occurred_at__isnull=True,
                created_date__date__gte=window_start,
                created_date__date__lte=window_end,
            )
        )
        if vessel_id:
            queryset = queryset.filter(vessel_id=vessel_id)
        return queryset
