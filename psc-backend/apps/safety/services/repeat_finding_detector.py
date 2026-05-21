from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from apps.safety.models import SOIFinding, SOIInspection
from apps.safety.services.fts_engine import SafetyFtsEngine


def _ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


@dataclass(frozen=True)
class RepeatFindingResult:
    is_repeat: bool
    occurrence_count: int
    badge_text: str | None
    previous_finding_id: int | None
    previous_closed_at: object | None
    window_days: int

    def to_payload(self) -> dict[str, object]:
        return {
            "is_repeat": self.is_repeat,
            "occurrence_count": self.occurrence_count,
            "badge_text": self.badge_text,
            "previous_finding_id": self.previous_finding_id,
            "previous_closed_at": self.previous_closed_at.isoformat() if hasattr(self.previous_closed_at, "isoformat") else self.previous_closed_at,
            "window_days": self.window_days,
        }


class RepeatFindingDetector:
    def __init__(
        self,
        *,
        finding_model=SOIFinding,
        inspection_model=SOIInspection,
        now_func=timezone.now,
        repeat_window_days: int = 180,
        dashboard_window_days: int = 365,
        fts_engine: SafetyFtsEngine | None = None,
    ) -> None:
        self.finding_model = finding_model
        self.inspection_model = inspection_model
        self.now_func = now_func
        self.repeat_window_days = repeat_window_days
        self.dashboard_window_days = dashboard_window_days
        self.fts_engine = fts_engine or SafetyFtsEngine()

    def detect(self, finding: SOIFinding, *, reference_at=None) -> RepeatFindingResult:
        if finding.item_id in (None, ""):
            return self._empty_result()

        vessel_id = self._resolve_vessel_id(finding.inspection_id)
        if not vessel_id:
            return self._empty_result()

        effective_at = reference_at or finding.closed_at or finding.created_date or self.now_func()
        window_start = effective_at - timedelta(days=self.repeat_window_days)
        previous_qs = self.finding_model.objects.filter(
            inspection_id__in=self._inspection_ids_for_vessel(vessel_id),
            is_deleted=False,
            status=SOIFinding.Status.CLOSED,
            area_id=finding.area_id,
            item_id=finding.item_id,
            closed_at__isnull=False,
            closed_at__gte=window_start,
            closed_at__lt=effective_at,
        ).exclude(pk=finding.pk)
        previous_matches = [
            row
            for row in previous_qs.order_by("-closed_at", "-id")
            if self.fts_engine.descriptions_are_similar(
                self._finding_text(row),
                self._finding_text(finding),
            )
        ]
        previous_count = len(previous_matches)
        previous = previous_matches[0] if previous_matches else None

        if previous_count == 0:
            return RepeatFindingResult(
                is_repeat=False,
                occurrence_count=1,
                badge_text=None,
                previous_finding_id=None,
                previous_closed_at=None,
                window_days=self.repeat_window_days,
            )

        occurrence_count = previous_count + 1
        return RepeatFindingResult(
            is_repeat=True,
            occurrence_count=occurrence_count,
            badge_text=f"Repeat - {_ordinal(occurrence_count)} occurrence",
            previous_finding_id=previous.pk if previous is not None else None,
            previous_closed_at=previous.closed_at if previous is not None else None,
            window_days=self.repeat_window_days,
        )

    def top_repeat_findings_for_vessel(self, vessel_id: str, *, limit: int = 5) -> list[dict[str, object]]:
        window_start = self.now_func() - timedelta(days=self.dashboard_window_days)
        findings = list(
            self.finding_model.objects.filter(
                inspection_id__in=self._inspection_ids_for_vessel(vessel_id),
                is_deleted=False,
                status=SOIFinding.Status.CLOSED,
                item_id__isnull=False,
                closed_at__isnull=False,
                closed_at__gte=window_start,
            ).order_by("-closed_at", "-id")
        )

        clusters: list[dict[str, object]] = []
        for finding in findings:
            if finding.item_id in (None, ""):
                continue
            matched_cluster = None
            for cluster in clusters:
                if cluster["area_id"] != int(finding.area_id) or cluster["item_id"] != int(finding.item_id):
                    continue
                if self.fts_engine.descriptions_are_similar(
                    str(cluster["signature_text"]),
                    self._finding_text(finding),
                ):
                    matched_cluster = cluster
                    break
            if matched_cluster is None:
                clusters.append(
                    {
                        "area_id": int(finding.area_id),
                        "item_id": int(finding.item_id),
                        "count": 1,
                        "latest_closed_at": finding.closed_at,
                        "signature_text": self._finding_text(finding),
                    }
                )
                continue
            matched_cluster["count"] = int(matched_cluster["count"]) + 1
            if finding.closed_at and (
                matched_cluster["latest_closed_at"] is None
                or finding.closed_at > matched_cluster["latest_closed_at"]
            ):
                matched_cluster["latest_closed_at"] = finding.closed_at

        repeated_clusters = [
            cluster
            for cluster in clusters
            if int(cluster["count"]) > 1
        ]
        repeated_clusters = sorted(
            repeated_clusters,
            key=lambda cluster: (
                -int(cluster["count"]),
                -(cluster["latest_closed_at"].timestamp() if cluster["latest_closed_at"] else 0),
            ),
        )[:limit]
        return [
            {
                "area_id": int(cluster["area_id"]),
                "item_id": int(cluster["item_id"]),
                "occurrence_count": int(cluster["count"]),
                "badge_text": f"Repeat - {_ordinal(int(cluster['count']))} occurrence",
                "latest_closed_at": cluster["latest_closed_at"].isoformat()
                if hasattr(cluster["latest_closed_at"], "isoformat")
                else cluster["latest_closed_at"],
                "window_days": self.dashboard_window_days,
            }
            for cluster in repeated_clusters
        ]

    def _inspection_ids_for_vessel(self, vessel_id: str):
        return self.inspection_model.objects.filter(
            vessel_id=str(vessel_id),
            is_deleted=False,
        ).values("id")

    def _resolve_vessel_id(self, inspection_id: int) -> str | None:
        row = self.inspection_model.objects.filter(
            pk=inspection_id,
            is_deleted=False,
        ).values("vessel_id").first()
        if row is None:
            return None
        return str(row["vessel_id"])

    def _empty_result(self) -> RepeatFindingResult:
        return RepeatFindingResult(
            is_repeat=False,
            occurrence_count=1,
            badge_text=None,
            previous_finding_id=None,
            previous_closed_at=None,
            window_days=self.repeat_window_days,
        )

    @staticmethod
    def _finding_text(finding: SOIFinding) -> str:
        return " ".join(
            value.strip()
            for value in (
                str(getattr(finding, "title", "") or ""),
                str(getattr(finding, "description", "") or ""),
            )
            if value and value.strip()
        )
