from __future__ import annotations
from dataclasses import asdict, dataclass

from apps.safety.models import Incident, SOIFinding, SOIInspection, SafetyFieldHistory
from apps.safety.services.field_history_recorder import resolve_actor_id, resolve_actor_role
from apps.safety.services.life_threat_detector import LifeThreatScanResult


@dataclass(frozen=True)
class HighSeverityNudgeResult:
    incident_linked_id: int | None
    incident_linked_number: str | None
    incident_worthy_action: str | None
    incident_worthy_reason: str | None
    life_threat_detected: bool
    life_threat_escalation_target: str | None
    life_threat_keywords: tuple[str, ...]
    notifications_emitted: int
    record_type: str | None
    required: bool

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["life_threat_keywords"] = list(self.life_threat_keywords)
        return payload


class HighSeverityNudgeService:
    def requires_nudge(self, *, severity: str | None) -> bool:
        return str(severity or "").strip().upper() == SOIFinding.Severity.HIGH

    def resolve(
        self,
        *,
        finding: SOIFinding,
        inspection: SOIInspection,
        user,
        incident_worthy_action: str | None,
        incident_worthy_reason: str | None,
        life_threat_escalation_target: str | None,
        life_threat_result: LifeThreatScanResult,
    ) -> HighSeverityNudgeResult:
        normalized_action = self._normalize_choice(incident_worthy_action)
        normalized_reason = self._normalize_reason(incident_worthy_reason)
        normalized_target = self._normalize_target(life_threat_escalation_target)
        required = self.requires_nudge(severity=finding.severity)

        notifications_emitted = 0
        record_type = None

        if life_threat_result.detected:
            record_type = normalized_target
            self._append_history(
                finding,
                field_name="life_threat_keywords",
                new_value=list(life_threat_result.matched_keywords),
                user=user,
                change_reason="Life-threat escalation keywords detected during SOI finding save.",
            )
            self._append_history(
                finding,
                field_name="life_threat_escalation_target",
                new_value=normalized_target,
                user=user,
                change_reason="Life-threat escalation route selected.",
            )
        elif required:
            record_type = Incident.RecordType.INCIDENT if normalized_action == "CREATE_INCIDENT" else None
            self._append_history(
                finding,
                field_name="incident_worthy_action",
                new_value=normalized_action,
                user=user,
                change_reason="HIGH-severity incident-worthiness prompt resolved.",
            )
            if normalized_reason:
                self._append_history(
                    finding,
                    field_name="incident_worthy_reason",
                    new_value=normalized_reason,
                    user=user,
                    change_reason="HIGH-severity finding retained within SOI.",
                )

        return HighSeverityNudgeResult(
            incident_linked_id=None,
            incident_linked_number=None,
            incident_worthy_action=normalized_action,
            incident_worthy_reason=normalized_reason,
            life_threat_detected=life_threat_result.detected,
            life_threat_escalation_target=normalized_target,
            life_threat_keywords=life_threat_result.matched_keywords,
            notifications_emitted=notifications_emitted,
            record_type=record_type,
            required=required,
        )

    def _append_history(
        self,
        finding: SOIFinding,
        *,
        field_name: str,
        new_value: str | None,
        user,
        change_reason: str,
    ) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=finding._meta.db_table,
            parent_id=finding.pk,
            field_name=field_name,
            old_value=None,
            new_value=new_value,
            change_reason=change_reason,
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=finding.schema_version or 1,
        )

    def _normalize_choice(self, value: str | None) -> str | None:
        text = str(value or "").strip().upper()
        return text or None

    def _normalize_reason(self, value: str | None) -> str | None:
        text = str(value or "").strip()
        return text or None

    def _normalize_target(self, value: str | None) -> str | None:
        text = str(value or "").strip().upper()
        return text or None
