from __future__ import annotations
from dataclasses import dataclass

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.services.field_history_recorder import resolve_actor_id, resolve_actor_role


PHASE7_SIGNATURE_FIELD_PREFIX = "phase7_signature_"


@dataclass(frozen=True)
class SignaturePayload:
    typed_name: str
    device_fingerprint: str
    signed_at: object


class SignatureChainService:
    REPORTER = "REPORTER"
    MASTER = "MASTER"
    HOD = "HOD"
    DPA = "DPA"
    FM = "FM"
    PIC = "PIC"
    OFFICE_DECISION_ROLES = {DPA, PIC}

    ROLE_ALIASES = {
        REPORTER: {"REPORTER"},
        MASTER: {"MASTER"},
        HOD: {"HOD", "HEAD OF DEPARTMENT", "CE", "CHIEF ENGINEER", "CO", "CHIEF OFFICER"},
        DPA: {"DPA"},
        FM: {"FM", "FLEET MANAGER"},
        PIC: {"PIC", "VESSEL SUPERINTENDENT"},
    }
    ACCEPTANCE_PROCESS_IDS = ("SAF_P_004", "SAF_P_006")

    def validate_payload(self, *, typed_name: str, device_fingerprint: str) -> SignaturePayload:
        errors: dict[str, str] = {}
        normalized_name = (typed_name or "").strip()
        normalized_fingerprint = (device_fingerprint or "").strip()

        if len(normalized_name) < 3:
            errors["typed_name"] = "Digital signature requires the typed full name."
        if not normalized_fingerprint:
            errors["device_fingerprint"] = "Digital signature requires a device fingerprint."

        if errors:
            raise serializers.ValidationError(errors)

        return SignaturePayload(
            typed_name=normalized_name,
            device_fingerprint=normalized_fingerprint,
            signed_at=timezone.now(),
        )

    def closer_role(self, incident: Incident) -> str:
        return self.DPA

    def required_process_id(self, incident: Incident) -> str:
        return "SAF_P_004"

    def signature_status(self, incident: Incident) -> dict[str, dict[str, object]]:
        dpa_signed = bool(incident.dpa_accepted_at and incident.dpa_accepted_by)
        fm_signed = bool(incident.fm_approved_at and incident.fm_approved_by)
        return {
            "reporter": {
                "required": True,
                "present": self._reporter_signed(incident),
            },
            "master": {
                "required": True,
                "present": self._role_seen(incident, self.MASTER),
            },
            "hod": {
                "required": True,
                "present": self._role_seen(incident, self.HOD),
            },
            "dpa": {
                "required": True,
                "present": dpa_signed,
            },
            "fm": {
                "required": False,
                "present": fm_signed,
            },
            "pic": {
                "required": False,
                "present": self._phase7_role_signed(incident, self.PIC),
            },
        }

    def phase_seven_blockers(self, incident: Incident, *, action_role: str | None = None) -> list[str]:
        return []

    def stamp_phase7_signature(
        self,
        incident: Incident,
        *,
        role_code: str,
        typed_name: str,
        device_fingerprint: str,
        user,
    ) -> SignaturePayload:
        payload = self.validate_payload(
            typed_name=typed_name,
            device_fingerprint=device_fingerprint,
        )
        actor_id = resolve_actor_id(user)
        timestamp = payload.signed_at

        if role_code in {self.PIC, self.DPA}:
            incident.dpa_accepted_at = timestamp
            incident.dpa_accepted_by = actor_id
            incident.updated_by = actor_id
            incident.updated_date = timestamp
            incident.save(update_fields=["dpa_accepted_at", "dpa_accepted_by", "updated_by", "updated_date"])
        elif role_code == self.FM:
            incident.fm_approved_at = timestamp
            incident.fm_approved_by = actor_id
            incident.updated_by = actor_id
            incident.updated_date = timestamp
            incident.save(update_fields=["fm_approved_at", "fm_approved_by", "updated_by", "updated_date"])
        else:
            raise serializers.ValidationError({"role": "Unsupported Phase 7 signature role."})

        SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name=f"{PHASE7_SIGNATURE_FIELD_PREFIX}{role_code.lower()}",
            old_value=None,
            new_value={
                "typed_name": payload.typed_name,
                "signed_at": payload.signed_at.isoformat(),
                "device_fingerprint": payload.device_fingerprint,
                "signed_by": actor_id,
                "signed_role": resolve_actor_role(user),
            },
            actor_user_id=actor_id,
            actor_role_code=resolve_actor_role(user),
            schema_version=incident.schema_version or 1,
        )
        return payload

    def stamp_phase7_supporting_signature(
        self,
        incident: Incident,
        *,
        role_code: str,
        typed_name: str,
        device_fingerprint: str,
        user,
    ) -> SignaturePayload:
        if role_code not in {self.HOD, self.MASTER}:
            raise serializers.ValidationError({"role": "Unsupported supporting Phase 7 signature role."})

        payload = self.validate_payload(
            typed_name=typed_name,
            device_fingerprint=device_fingerprint,
        )
        actor_id = resolve_actor_id(user)

        SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name=f"{PHASE7_SIGNATURE_FIELD_PREFIX}{role_code.lower()}",
            old_value=None,
            new_value={
                "typed_name": payload.typed_name,
                "signed_at": payload.signed_at.isoformat(),
                "device_fingerprint": payload.device_fingerprint,
                "signed_by": actor_id,
                "signed_role": resolve_actor_role(user),
            },
            actor_user_id=actor_id,
            actor_role_code=resolve_actor_role(user),
            schema_version=incident.schema_version or 1,
        )
        return payload

    def _reporter_signed(self, incident: Incident) -> bool:
        return bool(
            (incident.reporter_id or "").strip()
            and (incident.reporter_name or "").strip()
            and incident.reported_at
            and (incident.reporter_device_fingerprint or "").strip()
        )

    def _role_seen(self, incident: Incident, role_code: str) -> bool:
        expected_roles = self.ROLE_ALIASES[role_code]
        phase_log_roles = {
            (row.actor_role_code or "").strip().upper()
            for row in incident.phase_logs.all().only("actor_role_code")
        }
        if phase_log_roles.intersection(expected_roles):
            return True

        history_roles = {
            (row.actor_role_code or "").strip().upper()
            for row in SafetyFieldHistory.objects.filter(
                parent_table=incident._meta.db_table,
                parent_id=incident.pk,
            ).only("actor_role_code")
        }
        return bool(history_roles.intersection(expected_roles))

    def _phase7_role_signed(self, incident: Incident, role_code: str) -> bool:
        return SafetyFieldHistory.objects.filter(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name=f"{PHASE7_SIGNATURE_FIELD_PREFIX}{role_code.lower()}",
        ).exists()
