from __future__ import annotations

from apps.safety.models import Incident
from apps.safety.repositories import IncidentRepository


def formalize_near_miss_number_for_office(
    near_miss: Incident,
    *,
    repository: IncidentRepository | None = None,
) -> bool:
    if near_miss.record_type != Incident.RecordType.NEAR_MISS:
        return False
    if near_miss.state != Incident.State.READY_FOR_OFFICE_COMMENTS:
        return False

    current_number = str(near_miss.incident_number or "").strip()
    if not current_number.startswith("DRAFT-"):
        return False

    repository = repository or IncidentRepository()
    formal_number = repository.assign_formal_number(near_miss)
    if formal_number == current_number:
        return False

    near_miss.incident_number = formal_number
    return True
