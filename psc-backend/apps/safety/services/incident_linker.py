from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

from django.db import transaction

from apps.safety.models import Incident


EARTH_RADIUS_NM = 3440.065


class IncidentLinkError(ValueError):
    """Raised when an incident linking operation violates the Step 1.6 contract."""


@dataclass(frozen=True)
class DuplicateCandidate:
    incident_id: int
    vessel_id: str
    distance_nm: float
    overlap_hours: float
    narrative_overlap: float


class IncidentLinker:
    def __init__(self, *, model_class=Incident) -> None:
        self.model_class = model_class

    def link_multi_vessel_incidents(self, incident_ids: Iterable[int]) -> tuple[Incident, Incident]:
        unique_ids = list(dict.fromkeys(int(incident_id) for incident_id in incident_ids))
        if len(unique_ids) != 2:
            raise IncidentLinkError("Multi-vessel linking requires exactly two distinct incidents.")

        incidents = list(self.model_class.objects.filter(pk__in=unique_ids, is_deleted=False).order_by("id"))
        if len(incidents) != 2:
            raise IncidentLinkError("One or more incidents could not be found for linking.")
        first, second = incidents
        if first.pk == second.pk:
            raise IncidentLinkError("An incident cannot be linked to itself.")
        if first.vessel_id == second.vessel_id:
            raise IncidentLinkError("Multi-vessel linking requires incidents from different vessels.")
        if first.linked_incident_id not in (None, second.pk) or second.linked_incident_id not in (None, first.pk):
            raise IncidentLinkError("Incidents already linked elsewhere cannot be re-linked into a cycle.")

        with transaction.atomic():
            first.linked_incident_id = second.pk
            second.linked_incident_id = first.pk
            first.save(update_fields=["linked_incident_id"])
            second.save(update_fields=["linked_incident_id"])

        return first, second

    def detect_duplicates(
        self,
        vessel_id: str,
        date_range: tuple[datetime, datetime],
        narrative_fingerprint: str,
        *,
        incident_type_id: int | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        source_incident_id: int | None = None,
    ) -> list[DuplicateCandidate]:
        start_at, end_at = date_range
        queryset = self.model_class.objects.filter(
            is_deleted=False,
            record_type=Incident.RecordType.INCIDENT,
            superseded_by_id__isnull=True,
            occurred_at__isnull=False,
            occurred_at__gte=start_at,
            occurred_at__lte=end_at,
        )
        if incident_type_id is not None:
            queryset = queryset.filter(incident_type_id=incident_type_id)
        if source_incident_id is not None:
            queryset = queryset.exclude(pk=source_incident_id)

        candidates: list[DuplicateCandidate] = []
        for incident in queryset.order_by("occurred_at", "id"):
            if latitude is not None and longitude is not None:
                if incident.latitude is None or incident.longitude is None:
                    continue
                distance_nm = self._distance_nm(
                    float(latitude),
                    float(longitude),
                    float(incident.latitude),
                    float(incident.longitude),
                )
                if distance_nm > 10:
                    continue
            else:
                distance_nm = 0.0

            overlap_hours = abs((incident.occurred_at - start_at).total_seconds()) / 3600
            overlap_hours = min(overlap_hours, abs((end_at - incident.occurred_at).total_seconds()) / 3600)
            if overlap_hours > 24:
                continue

            overlap = self._narrative_overlap(narrative_fingerprint, incident.narrative or "")
            if incident.vessel_id != str(vessel_id) and overlap == 0.0:
                # Cross-vessel candidates need either narrative similarity or explicit spatial match.
                continue
            candidates.append(
                DuplicateCandidate(
                    incident_id=incident.pk,
                    vessel_id=str(incident.vessel_id),
                    distance_nm=round(distance_nm, 2),
                    overlap_hours=round(overlap_hours, 2),
                    narrative_overlap=round(overlap, 2),
                )
            )

        return candidates

    @staticmethod
    def _distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, (lat1, lon1, lat2, lon2))
        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad
        haversine = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        return 2 * EARTH_RADIUS_NM * asin(sqrt(haversine))

    @staticmethod
    def _narrative_overlap(left: str, right: str) -> float:
        left_tokens = {token for token in left.lower().split() if len(token) > 2}
        right_tokens = {token for token in right.lower().split() if len(token) > 2}
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
