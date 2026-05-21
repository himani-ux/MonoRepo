from __future__ import annotations

from django.db import DatabaseError
from rest_framework import serializers

from apps.safety.models import SOIOfficerSetting
from apps.safety.repositories.cms_repo import CMSRepository
from apps.safety.services.crew_rank_resolver import CrewRankResolver
from apps.safety.services.soi_officer_setting_table import ensure_soi_officer_setting_table


DEFAULT_SAFETY_OFFICER_RANKS = {"CO", "CHIEF OFFICER"}
ALTERNATE_SAFETY_OFFICER_RANKS = {"2/E", "2E", "SECOND ENGINEER"}
SAFETY_OFFICER_ACTOR_ROLES = DEFAULT_SAFETY_OFFICER_RANKS | {"SO", "SAFETY OFFICER"}
_DEPARTMENT_CODE_ALIASES = (
    ("ENGINE", "ENGINE"),
    ("DECK", "DECK"),
    ("CATER", "CATERING"),
    ("GALLEY", "CATERING"),
    ("ELECT", "ELECTRICAL"),
)


class SOIAssistantValidator:
    def __init__(
        self,
        *,
        cms_repository: CMSRepository | None = None,
        crew_rank_resolver: CrewRankResolver | None = None,
        officer_setting_model=SOIOfficerSetting,
    ) -> None:
        repository = cms_repository or CMSRepository()
        self.cms_repository = repository
        self.crew_rank_resolver = crew_rank_resolver or CrewRankResolver(cms_repository=repository)
        self.officer_setting_model = officer_setting_model

    def resolve_safety_officer(
        self,
        *,
        vessel_id: str,
        actor_id: str,
        actor_role: str,
        requested_safety_officer_crew_id: str | None = None,
        active_on=None,
    ) -> dict[str, object]:
        normalized_actor_id = str(actor_id or "").strip()
        normalized_actor_role = str(actor_role or "").strip().upper()
        requested_id = str(requested_safety_officer_crew_id or "").strip()

        if normalized_actor_role in DEFAULT_SAFETY_OFFICER_RANKS | {"SO", "SAFETY OFFICER"}:
            snapshot = self.crew_rank_resolver.resolve_snapshot(
                vessel_id=str(vessel_id),
                crew_id=normalized_actor_id,
                at_timestamp=active_on,
            )
            if snapshot is None:
                raise serializers.ValidationError(
                    {"safety_officer_crew_id": "Authenticated Safety Officer is not active on this vessel in CMS."}
                )
            rank = str(snapshot.get("rank") or "").strip().upper()
            if rank not in DEFAULT_SAFETY_OFFICER_RANKS:
                raise serializers.ValidationError(
                    {"safety_officer_crew_id": "Default Safety Officer must resolve to the active CO in CMS."}
                )
            if requested_id and requested_id != normalized_actor_id:
                raise serializers.ValidationError(
                    {"safety_officer_crew_id": "Safety Officer identity is derived server-side; spoofed value rejected."}
                )
            return snapshot

        if normalized_actor_role in ALTERNATE_SAFETY_OFFICER_RANKS:
            try:
                setting = self.officer_setting_model.objects.filter(
                    vessel_id=str(vessel_id),
                    alternate_enabled=True,
                ).first()
            except DatabaseError:
                ensure_soi_officer_setting_table()
                setting = self.officer_setting_model.objects.filter(
                    vessel_id=str(vessel_id),
                    alternate_enabled=True,
                ).first()
            if setting is None or str(setting.alternate_so_crew_id or "").strip() != normalized_actor_id:
                raise serializers.ValidationError(
                    {
                        "safety_officer_crew_id": (
                            "2/E alternate Safety Officer is not enabled by Master for this vessel."
                        )
                    }
                )
            snapshot = self.crew_rank_resolver.resolve_snapshot(
                vessel_id=str(vessel_id),
                crew_id=normalized_actor_id,
                at_timestamp=active_on,
            )
            if snapshot is None:
                raise serializers.ValidationError(
                    {"safety_officer_crew_id": "Alternate Safety Officer is not active on this vessel in CMS."}
                )
            rank = str(snapshot.get("rank") or "").strip().upper()
            if rank not in ALTERNATE_SAFETY_OFFICER_RANKS:
                raise serializers.ValidationError(
                    {"safety_officer_crew_id": "Master-enabled alternate Safety Officer must resolve to active 2/E in CMS."}
                )
            if requested_id and requested_id != normalized_actor_id:
                raise serializers.ValidationError(
                    {"safety_officer_crew_id": "Safety Officer identity is derived server-side; spoofed value rejected."}
                )
            return snapshot

        raise serializers.ValidationError({"role": "SOI creation is restricted to the active Safety Officer."})

    def validate_trainees(
        self,
        *,
        vessel_id: str,
        trainee_crew_ids: list[str],
        safety_officer_crew_id: str,
        assistant_crew_id: str,
        active_on=None,
    ) -> list[str]:
        normalized = [str(crew_id).strip() for crew_id in trainee_crew_ids if str(crew_id).strip()]
        if len(normalized) > 3:
            raise serializers.ValidationError({"trainee_crew_ids": "A maximum of 3 trainees may be assigned."})
        if len(set(normalized)) != len(normalized):
            raise serializers.ValidationError({"trainee_crew_ids": "Trainee crew ids must be unique."})

        blocked = {str(safety_officer_crew_id).strip(), str(assistant_crew_id).strip()}
        for crew_id in normalized:
            if crew_id in blocked:
                raise serializers.ValidationError(
                    {"trainee_crew_ids": "Trainees cannot duplicate the Safety Officer or Assistant."}
                )
            snapshot = self.crew_rank_resolver.resolve_snapshot(
                vessel_id=str(vessel_id),
                crew_id=crew_id,
                at_timestamp=active_on,
            )
            if snapshot is None:
                raise serializers.ValidationError(
                    {"trainee_crew_ids": f"Trainee {crew_id} is not active on this vessel in CMS."}
                )
        return normalized

    def resolve_assignments(
        self,
        *,
        vessel_id: str,
        safety_officer_crew_id: str,
        assistant_crew_id: str,
        active_on=None,
    ) -> dict[str, str]:
        safety_officer = self.crew_rank_resolver.resolve_snapshot(
            vessel_id=str(vessel_id),
            crew_id=str(safety_officer_crew_id),
            at_timestamp=active_on,
        )
        if safety_officer is None:
            raise serializers.ValidationError(
                {"safety_officer_crew_id": "Safety Officer must be a current CMS crew member for the vessel."}
            )

        assistant = self.crew_rank_resolver.resolve_snapshot(
            vessel_id=str(vessel_id),
            crew_id=str(assistant_crew_id),
            at_timestamp=active_on,
        )
        if assistant is None:
            raise serializers.ValidationError(
                {"assistant_crew_id": "Assistant must be a current CMS crew member for the vessel."}
            )

        safety_officer_department = self._normalize_department_code(safety_officer.get("department"))
        assistant_department = self._normalize_department_code(assistant.get("department"))
        if not safety_officer_department:
            raise serializers.ValidationError(
                {"safety_officer_crew_id": "Safety Officer department could not be resolved from CMS."}
            )
        if not assistant_department:
            raise serializers.ValidationError(
                {"assistant_crew_id": "Assistant department could not be resolved from CMS."}
            )
        if safety_officer_department == assistant_department:
            raise serializers.ValidationError(
                {
                    "assistant_crew_id": (
                        "Assistant must be from a different department than the Safety Officer (D-SOI-08)."
                    )
                }
            )

        return {
            "assistant_department": assistant_department,
            "assistant_rank": str(assistant.get("rank") or "").strip().upper(),
            "safety_officer_department": safety_officer_department,
            "safety_officer_rank": str(safety_officer.get("rank") or "").strip().upper(),
        }

    def _normalize_department_code(self, value: object) -> str:
        department = str(value or "").strip().upper()
        if not department:
            return ""
        for needle, code in _DEPARTMENT_CODE_ALIASES:
            if needle in department:
                return code
        return department[:16]
