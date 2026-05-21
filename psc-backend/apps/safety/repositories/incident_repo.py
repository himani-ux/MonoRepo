from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import TYPE_CHECKING

from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone

from apps.safety.models import Incident

from .base import BaseRepository

if TYPE_CHECKING:
    from apps.safety.services.mscmepc3_position_fetcher import Mscmepc3PositionFetcher


class IncidentRepository(BaseRepository):
    INCIDENT_NUMBER_RETRY_ATTEMPTS = 5

    def __init__(
        self,
        *,
        model_class=Incident,
        position_fetcher: "Mscmepc3PositionFetcher | None" = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.model_class = model_class
        if position_fetcher is None:
            from apps.safety.services.mscmepc3_position_fetcher import Mscmepc3PositionFetcher

            position_fetcher = Mscmepc3PositionFetcher()
        self.position_fetcher = position_fetcher

    def create(self, payload: Mapping[str, object]) -> Incident:
        data = dict(payload)
        vessel_code = self._normalize_vessel_code(data.pop("vessel_code", None), data.get("vessel_id"))
        year = self._resolve_year(data)
        incident_number_supplied = bool(data.get("incident_number"))

        data.setdefault("record_type", Incident.RecordType.INCIDENT)
        data.setdefault("state", Incident.State.DRAFT)
        data.setdefault("current_phase", 1)
        data.setdefault("schema_version", Incident.ENUM_TIGHTENED_SCHEMA_VERSION)
        data.setdefault("reported_at", timezone.now())
        data.setdefault("updated_by", data.get("created_by"))
        data = self.position_fetcher.enrich_payload(data)

        for attempt in range(self.INCIDENT_NUMBER_RETRY_ATTEMPTS):
            if not incident_number_supplied:
                data["incident_number"] = self.allocate_draft_reference(
                    vessel_code=vessel_code,
                    year=year,
                )
            try:
                return self.model_class.objects.create(**data)
            except IntegrityError as exc:
                if incident_number_supplied or not self._is_incident_number_collision(exc):
                    raise
                if attempt == self.INCIDENT_NUMBER_RETRY_ATTEMPTS - 1:
                    raise

        raise RuntimeError("Unable to allocate a unique incident number.")

    def read(self, incident_id: int) -> Incident | None:
        return self.model_class.objects.filter(pk=incident_id, is_deleted=False).first()

    def update(self, incident_id: int, changes: Mapping[str, object]) -> Incident:
        incident = self.model_class.objects.get(pk=incident_id, is_deleted=False)
        data = dict(changes)
        data.pop("vessel_code", None)
        data.setdefault("updated_date", timezone.now())
        if {"vessel_id", "occurred_at", "latitude", "longitude"} & set(data.keys()):
            data = self.position_fetcher.enrich_payload(data)
        for field_name, value in data.items():
            setattr(incident, field_name, value)
        incident.save()
        return incident

    def list_by_vessel(
        self,
        vessel_id: str | None = None,
        *,
        filters: Mapping[str, object] | None = None,
    ):
        queryset = self.model_class.objects.filter(is_deleted=False)
        if vessel_id is not None:
            queryset = queryset.filter(vessel_id=str(vessel_id))

        filters = filters or {}
        for field_name in ("risk_band", "record_type", "state"):
            value = filters.get(field_name)
            if value not in (None, ""):
                queryset = queryset.filter(**{field_name: value})

        date_from = filters.get("date_from")
        if date_from not in (None, ""):
            queryset = queryset.filter(occurred_at__date__gte=date_from)

        date_to = filters.get("date_to")
        if date_to not in (None, ""):
            queryset = queryset.filter(occurred_at__date__lte=date_to)

        return queryset.order_by("-created_date", "-id")

    def get_by_number(self, incident_number: str) -> Incident | None:
        return self.model_class.objects.filter(
            incident_number=incident_number,
            is_deleted=False,
        ).first()

    def assign_number(self, vessel_code: str, year: int) -> str:
        prefix = f"{vessel_code}/{year}/"
        with transaction.atomic():
            numbers = list(
                self.model_class.objects.select_for_update()
                .filter(incident_number__startswith=prefix)
                .values_list("incident_number", flat=True)
            )
            next_sequence = self._next_sequence(numbers, prefix)
            return f"{prefix}{next_sequence:03d}"

    def assign_formal_number(self, incident: Incident) -> str:
        vessel_code, year = self.resolve_number_context(incident)
        if incident.incident_number and not incident.incident_number.startswith("DRAFT-"):
            return incident.incident_number
        return self.assign_number(vessel_code, year)

    def allocate_draft_reference(self, vessel_code: str, year: int) -> str:
        prefix = f"DRAFT-{vessel_code}/{year}/T"
        with transaction.atomic():
            numbers = list(
                self.model_class.objects.select_for_update()
                .filter(incident_number__startswith=prefix)
                .values_list("incident_number", flat=True)
            )
            next_sequence = self._next_sequence(numbers, prefix)
            return f"{prefix}{next_sequence:03d}"

    def resolve_number_context(self, incident: Incident) -> tuple[str, int]:
        number = (incident.incident_number or "").strip()
        if number.startswith("DRAFT-"):
            body = number[len("DRAFT-") :]
            parts = body.split("/")
            if len(parts) >= 2 and parts[1].isdigit():
                return parts[0], int(parts[1])
        elif number:
            parts = number.split("/")
            if len(parts) >= 2 and parts[1].isdigit():
                return parts[0], int(parts[1])

        vessel_code = self._normalize_vessel_code(None, incident.vessel_id)
        year = self._resolve_year(
            {
                "occurred_at": incident.occurred_at,
                "reported_at": incident.reported_at,
            }
        )
        return vessel_code, year

    def _next_sequence(self, numbers: list[str], prefix: str) -> int:
        highest = 0
        for number in numbers:
            if not number.startswith(prefix):
                continue
            suffix = number[len(prefix) :]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
        return highest + 1

    def _is_incident_number_collision(self, exc: IntegrityError) -> bool:
        message = str(exc)
        return (
            "uq_vims_safety_incident_number" in message
            or "incident_number" in message
            or "Cannot insert duplicate key" in message
        )

    def _normalize_vessel_code(self, explicit_code: object, vessel_id: object) -> str:
        for candidate in (explicit_code, vessel_id):
            if candidate is None:
                continue
            text = str(candidate).strip().upper()
            if text:
                return text
        return "UNKNOWN"

    def _resolve_year(self, data: Mapping[str, object]) -> int:
        for key in ("occurred_at", "reported_at"):
            value = data.get(key)
            if isinstance(value, datetime):
                return value.year
            if isinstance(value, date):
                return value.year
        return timezone.now().year
