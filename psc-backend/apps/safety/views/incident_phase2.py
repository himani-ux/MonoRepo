from __future__ import annotations

import json

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.models import Incident
from apps.safety.serializers.incident_phase2 import IncidentPhase2Serializer, IncidentPhase2SubmitSerializer
from apps.safety.services import (
    EvidenceDeadlineScheduler,
    NotificationWriter,
    capture_model_state,
    classify_band,
    record_field_changes,
)
from apps.safety.views.incident import IncidentViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_PHASE_2_MUTATION_ROLES = {
    "MASTER",
    "CO",
    "CE",
    "DPA",
    "FM",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "FLEET MANAGER",
}
ROLE_BASED_PIC_RECIPIENT = "OFFICE_PIC"


class IncidentPhase2ViewMixin(IncidentViewMixin):
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_002")
    notification_writer_class = NotificationWriter
    deadline_scheduler_class = EvidenceDeadlineScheduler

    def get_notification_writer(self) -> NotificationWriter:
        return self.notification_writer_class()

    def get_deadline_scheduler(self) -> EvidenceDeadlineScheduler:
        return self.deadline_scheduler_class()

    def _enforce_phase_2_mutation_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_PHASE_2_MUTATION_ROLES:
            raise PermissionDenied("Only Master, CO, CE, DPA, or FM may edit Phase 2 incident resources.")

    def _resolve_phase_2_pic_recipient(self, incident: Incident) -> str:
        existing_recipient = (incident.pic_user_id or "").strip()
        return existing_recipient or ROLE_BASED_PIC_RECIPIENT

    def _build_phase_2_notification_recipients(self, incident: Incident) -> list[str]:
        recipients = [self._resolve_phase_2_pic_recipient(incident), "DPA", "SAFETY_CHANNEL"]
        if incident.risk_band == Incident.RiskBand.RED:
            recipients.extend(["FM", "MANAGING_DIRECTOR"])
        return [recipient for recipient in recipients if recipient]

    def _resolve_closure_authority(self, incident: Incident) -> str:
        if incident.risk_band == Incident.RiskBand.RED:
            return "FM"
        if incident.risk_band == Incident.RiskBand.YELLOW:
            return "DPA"
        return "PIC"


class IncidentPhase2UpdateView(IncidentPhase2ViewMixin, generics.RetrieveUpdateAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentPhase2Serializer

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_object(self):
        incident = super().get_object()
        self._enforce_phase_reached_for_edit(incident, 2, "Phase 2 resources")
        return incident

    def perform_update(self, serializer):
        incident = self.get_object()
        self._enforce_phase_2_mutation_role()
        tracked_fields = tuple(serializer.validated_data.keys())
        old_state = capture_model_state(incident, field_names=tracked_fields)
        updated = serializer.save(updated_by=_resolve_actor_id(self.request.user))
        record_field_changes(
            updated,
            old_state,
            user=self.request.user,
            field_names=tracked_fields,
        )


class IncidentPhase2SubmitView(IncidentPhase2ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = IncidentPhase2SubmitSerializer

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        if incident.current_phase != 2:
            raise ValidationError("Only Phase 2 incidents can be submitted through this endpoint.")

        self._enforce_phase_2_mutation_role()
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "incident": incident},
        )
        serializer.is_valid(raise_exception=True)

        incident_repository = self.get_incident_repository()
        advisory = classify_band(loss_type=incident.loss_type_primary_id)
        submitted_at = timezone.now()
        old_state = capture_model_state(
            incident,
            field_names=(
                "incident_number",
                "state",
                "pic_user_id",
                "resources_allocated",
                "office_notified",
                "office_notification_mode",
                "dpa_notified_at",
                "fm_notified_at",
                "office_notified_at",
                "notification_channel_count",
                "slack_notified_at",
                "updated_by",
                "updated_date",
            ),
        )

        incident.incident_number = incident_repository.assign_formal_number(incident)
        incident.pic_user_id = self._resolve_phase_2_pic_recipient(incident)
        incident.resources_allocated = json.dumps(
            {
                "pic_user_id": incident.pic_user_id,
                "closure_authority_role": self._resolve_closure_authority(incident),
                "advisory_band": advisory.band,
                "office_notified": incident.office_notified,
                "office_notification_mode": incident.office_notification_mode,
            },
            sort_keys=True,
        )
        incident.office_notified_at = submitted_at
        incident.dpa_notified_at = submitted_at
        if incident.risk_band == Incident.RiskBand.RED:
            incident.fm_notified_at = submitted_at

        recipients = self._build_phase_2_notification_recipients(incident)
        notification_dispatch = self.get_notification_writer().dispatch_notification(
            record_id=incident.pk,
            recipients=recipients,
            kind="INCIDENT_PHASE_2_SUBMITTED",
            title="Incident submitted to office",
            message=f"Incident {incident.incident_number} is ready for root-cause entry.",
            payload={
                "incident_id": incident.pk,
                "incident_number": incident.incident_number,
                "risk_band": incident.risk_band,
                "imo_classifier": incident.imo_classifier,
                "current_phase": 3,
            },
            send_slack=True,
        )
        notification_rows = notification_dispatch.notification_rows
        incident.notification_channel_count = len(notification_rows)
        if notification_dispatch.slack_delivered:
            incident.slack_notified_at = submitted_at
        incident.state = "IN_PROGRESS"
        incident.updated_by = _resolve_actor_id(request.user)
        incident.updated_date = submitted_at
        incident.save(
            update_fields=[
                "incident_number",
                "pic_user_id",
                "resources_allocated",
                "office_notified",
                "office_notification_mode",
                "office_notified_at",
                "dpa_notified_at",
                "fm_notified_at",
                "notification_channel_count",
                "slack_notified_at",
                "state",
                "updated_by",
                "updated_date",
            ]
        )
        deadline_tasks = self.get_deadline_scheduler().schedule_default_tasks(
            incident,
            created_by=incident.updated_by,
        )
        record_field_changes(
            incident,
            old_state,
            user=request.user,
            field_names=tuple(old_state.keys()),
            change_reason="Phase 2 submit",
        )

        transition = self.get_phase_state_machine().transition(incident.pk, 3, request.user)
        incident.refresh_from_db()
        payload = IncidentPhase2Serializer(incident, context=self.get_serializer_context()).data
        payload["transition"] = transition
        payload["notifications_emitted"] = len(notification_rows)
        payload["deadline_tasks_created"] = len(deadline_tasks)
        return Response(payload, status=status.HTTP_200_OK)
