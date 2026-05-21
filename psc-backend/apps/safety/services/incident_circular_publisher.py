from __future__ import annotations
from dataclasses import dataclass

from rest_framework.exceptions import ValidationError

from apps.safety.models import Incident, Recommendation, SafetyFieldHistory
from apps.safety.services.field_history_recorder import resolve_actor_id, resolve_actor_role


@dataclass(frozen=True)
class CircularPublishResult:
    status: str
    circular_id: str | None
    detail_url: str | None
    payload: dict[str, object]


class WorkspaceCircularModuleClient:
    def publish_draft(self, *, payload: dict[str, object]) -> CircularPublishResult:
        source_id = payload["source_record_id"]
        source_type = str(payload.get("source_record_type") or "INCIDENT").lower().replace("_", "-")
        return CircularPublishResult(
            status="WORKSPACE_SEAM",
            circular_id=f"workspace-{source_type}-{source_id}",
            detail_url=None,
            payload=payload,
        )


class IncidentCircularPublisher:
    client_class = WorkspaceCircularModuleClient

    def __init__(self, *, client: object | None = None) -> None:
        self.client = client or self.client_class()

    def publish_from_incident(self, *, incident: Incident, user) -> CircularPublishResult:
        self._validate_incident(incident)
        lessons_rows = list(
            incident.recommendations.filter(
                is_deleted=False,
                tier=Recommendation.Tier.LESSONS_LEARNT,
            ).order_by("id")
        )
        if not lessons_rows:
            raise ValidationError("Closed incidents need at least one lessons-learned recommendation before Circular publish.")

        payload = self.build_payload(incident=incident, lessons_rows=lessons_rows)
        result = self.client.publish_draft(payload=payload)
        self._record_publish_history(incident=incident, user=user, result=result)
        return result

    def build_payload(
        self,
        *,
        incident: Incident,
        lessons_rows: list[Recommendation],
    ) -> dict[str, object]:
        summary = " ".join((row.title or "").strip() for row in lessons_rows if (row.title or "").strip())
        body_sections = [
            "\n".join(
                part
                for part in (
                    (row.title or "").strip(),
                    (row.description or "").strip(),
                    (row.rationale or "").strip(),
                )
                if part
            )
            for row in lessons_rows
        ]
        return {
            "source_module": "SAFETY",
            "source_record_type": "INCIDENT",
            "source_record_id": incident.pk,
            "source_reference": incident.incident_number,
            "title": f"Lessons learned draft - {incident.incident_number}",
            "summary": summary[:512],
            "body": "\n\n".join(section for section in body_sections if section),
            "closure_reason": incident.closure_reason or "",
            "risk_band": incident.risk_band,
            "imo_classifier": incident.imo_classifier,
            "closed_at": incident.closed_at.isoformat() if incident.closed_at is not None else None,
            "vessel_id": str(incident.vessel_id),
            "recommendation_ids": [row.pk for row in lessons_rows],
        }

    def _validate_incident(self, incident: Incident) -> None:
        if incident.record_type != Incident.RecordType.INCIDENT:
            raise ValidationError("Circular publish is only available for incident records.")
        if incident.state != "CLOSED" or incident.closed_at is None:
            raise ValidationError("Circular publish is only available after incident closure.")

    def _record_publish_history(self, *, incident: Incident, user, result: CircularPublishResult) -> None:
        actor_id = resolve_actor_id(user)
        actor_role = resolve_actor_role(user)
        SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name="incident_circular_publish",
            old_value=None,
            new_value={
                "status": result.status,
                "circular_id": result.circular_id,
                "detail_url": result.detail_url,
                "payload": result.payload,
            },
            change_reason="Closed incident lessons published to Circular module seam.",
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            schema_version=incident.schema_version or 1,
        )
