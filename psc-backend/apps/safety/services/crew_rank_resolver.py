from __future__ import annotations

from datetime import date, datetime

from apps.safety.repositories.cms_repo import CMSRepository


class CrewRankResolver:
    def __init__(self, *, cms_repository: CMSRepository | None = None) -> None:
        self.cms_repository = cms_repository or CMSRepository()

    def resolve_snapshot(
        self,
        *,
        vessel_id: str,
        crew_id: str,
        at_timestamp: date | datetime | str | None = None,
    ) -> dict[str, object] | None:
        return self.cms_repository.get_current_crew_snapshot(
            vessel_id=str(vessel_id),
            crew_id=str(crew_id),
            active_on=at_timestamp,
        )

    def list_vessel_crew(
        self,
        *,
        vessel_id: str,
        at_timestamp: date | datetime | str | None = None,
        exclude_department: str | None = None,
        exclude_crew_id: str | None = None,
    ) -> list[dict[str, object]]:
        return self.cms_repository.list_current_vessel_crew(
            vessel_id=str(vessel_id),
            active_on=at_timestamp,
            exclude_department=exclude_department,
            exclude_crew_id=exclude_crew_id,
        )
