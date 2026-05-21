from __future__ import annotations

from django.utils import timezone

from apps.safety.models import Incident
from apps.safety.repositories import IncidentRepository


class NearMissSupersedeError(ValueError):
    """Raised when a near-miss cannot be superseded into a new incident."""


class NearMissSupersedeService:
    def __init__(self, *, incident_repository: IncidentRepository | None = None, model_class=Incident) -> None:
        self.incident_repository = incident_repository or IncidentRepository(model_class=model_class)
        self.model_class = model_class

    def supersede_near_miss(self, near_miss_id: int, *, actor_id: str) -> Incident:
        near_miss = self.model_class.objects.get(pk=near_miss_id, is_deleted=False)
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise NearMissSupersedeError("Only near-miss records can be superseded into incidents.")
        if near_miss.superseded_by_id:
            raise NearMissSupersedeError("This near-miss has already been superseded.")

        payload = {
            "vessel_id": near_miss.vessel_id,
            "vessel_code": self.incident_repository.resolve_number_context(near_miss)[0],
            "record_type": Incident.RecordType.INCIDENT,
            "state": "DRAFT",
            "current_phase": 1,
            "schema_version": near_miss.schema_version or 1,
            "created_by": actor_id,
            "updated_by": actor_id,
            "occurred_at": near_miss.occurred_at,
            "reported_at": near_miss.reported_at or timezone.now(),
            "incident_type_id": near_miss.incident_type_id,
            "loss_type_primary_id": near_miss.loss_type_primary_id,
            "narrative": near_miss.narrative,
            "latitude": near_miss.latitude,
            "longitude": near_miss.longitude,
            "position_source": near_miss.position_source,
            "position_daily_report_id": near_miss.position_daily_report_id,
            "reporter_id": near_miss.reporter_id,
            "reporter_name": near_miss.reporter_name,
            "reporter_rank": near_miss.reporter_rank,
            "reporter_email": near_miss.reporter_email,
            "reporter_department": near_miss.reporter_department,
            "reporter_device_fingerprint": near_miss.reporter_device_fingerprint,
        }
        new_incident = self.incident_repository.create(payload)
        new_incident.linked_incident_id = near_miss.pk
        new_incident.save(update_fields=["linked_incident_id"])

        near_miss.state = "SUPERSEDED"
        near_miss.superseded_by_id = new_incident.pk
        near_miss.linked_incident_id = new_incident.pk
        near_miss.updated_by = actor_id
        near_miss.updated_date = timezone.now()
        near_miss.save(
            update_fields=[
                "state",
                "superseded_by_id",
                "linked_incident_id",
                "updated_by",
                "updated_date",
            ]
        )
        return new_incident
