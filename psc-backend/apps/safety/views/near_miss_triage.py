from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasAnyProcessPermission
from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.serializers import (
    IncidentSerializer,
    NearMissSerializer,
    NearMissTriageSerializer,
    PhaseLogSerializer,
)
from apps.safety.services import NearMissSupersedeError, NearMissSupersedeService, capture_model_state, record_field_changes
from apps.safety.views.near_miss import NearMissViewMixin, _normalized_role, _resolve_actor_id


PIC_OFFICE_ROLES = {"PIC", "OFFICE_PIC", "OFFICE_SSQE", "OFFICE_SUPT", "VESSEL SUPERINTENDENT"}


class NearMissTriageView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissTriageSerializer
    process_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_002", "SAF_P_006")
    near_miss_supersede_service_class = NearMissSupersedeService

    def get_permissions(self):
        return [self.form_permission_class(), self.process_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def _enforce_office_comment_role(self, *, priority: str | None, action: str) -> None:
        role = _normalized_role(self.request.user)
        if action in {"SEND_BACK", "REJECT"}:
            if role == "DPA" or role in PIC_OFFICE_ROLES:
                return
            raise PermissionDenied("Only the assigned office reviewer can send this near miss back or reject it.")
        if role == "DPA" or role in PIC_OFFICE_ROLES:
            return
        raise PermissionDenied("Near misses must be accepted by an authorized office reviewer.")

    def patch(self, request, *args, **kwargs):
        near_miss = self.get_object()
        if near_miss.state != Incident.State.READY_FOR_OFFICE_COMMENTS:
            raise ValidationError(
                "Near miss must complete vessel-side HOD/Master review before office comments."
            )

        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "incident": near_miss},
        )
        serializer.is_valid(raise_exception=True)

        actor_id = _resolve_actor_id(request.user)
        action = serializer.validated_data["action"]
        priority = serializer.validated_data.get("near_miss_priority")
        office_comment = serializer.validated_data.get("office_comment") or serializer.validated_data.get("override_reason")
        priority_change_reason = serializer.validated_data.get("priority_change_reason") or ""
        category_tag_change_reason = serializer.validated_data.get("category_tag_change_reason") or ""
        decision_reason_parts = [
            f"Priority change: {priority_change_reason}" if priority_change_reason else "",
            f"Category change: {category_tag_change_reason}" if category_tag_change_reason else "",
            f"Office comment: {office_comment}" if office_comment else "",
        ]
        decision_reason = " | ".join(part for part in decision_reason_parts if part)
        self._enforce_office_comment_role(priority=priority, action=action)

        if action in {"SEND_BACK", "REJECT"}:
            old_state = capture_model_state(
                near_miss,
                field_names=("state", "updated_by", "updated_date"),
            )
            near_miss.state = (
                Incident.State.REJECTED
                if action == "REJECT"
                else Incident.State.REWORK_REQUIRED
            )
            near_miss.updated_by = actor_id
            near_miss.updated_date = timezone.now()
            near_miss.save(update_fields=("state", "updated_by", "updated_date"))
            phase_log = IncidentPhaseLog.objects.create(
                incident=near_miss,
                phase_from=near_miss.current_phase,
                phase_to=near_miss.current_phase,
                transition_type=IncidentPhaseLog.TransitionType.REWORK,
                loop_back_reason=office_comment,
                actor_user_id=actor_id,
                actor_role_code=_normalized_role(request.user) or "OFFICE_REVIEWER",
                device_fingerprint=getattr(near_miss, "reporter_device_fingerprint", None),
                schema_version=near_miss.schema_version or 1,
            )
            record_field_changes(
                near_miss,
                old_state,
                user=request.user,
                field_names=("state", "updated_by", "updated_date"),
                change_reason=office_comment,
            )
            payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
            payload["office_comment_phase_log"] = PhaseLogSerializer(phase_log).data
            if action == "REJECT":
                payload["office_rejected_phase_log"] = payload["office_comment_phase_log"]
            return Response(payload, status=status.HTTP_200_OK)

        supersede_to_incident = serializer.validated_data.get("supersede_to_incident", False)
        suggestion = serializer.validated_data["suggestion"]

        tracked_fields = (
            "near_miss_priority",
            "near_miss_shell_tag",
            "near_miss_category_tags",
            "near_miss_mscat_category_id",
            "near_miss_mscat_subcode_id",
            "near_miss_mscat_subcode_ids",
            "office_comment",
            "state",
            "superseded_by_id",
            "linked_incident_id",
            "updated_by",
            "updated_date",
        )
        old_state = capture_model_state(near_miss, field_names=tracked_fields)

        near_miss.near_miss_priority = priority
        if "near_miss_shell_tag" in serializer.validated_data:
            near_miss.near_miss_shell_tag = serializer.validated_data["near_miss_shell_tag"]
            near_miss.near_miss_category_tags = serializer.validated_data["near_miss_category_tags"]
        if "near_miss_mscat_subcode_id" in serializer.validated_data:
            near_miss.near_miss_mscat_subcode_id = serializer.validated_data["near_miss_mscat_subcode_id"]
            near_miss.near_miss_mscat_category_id = serializer.validated_data["near_miss_mscat_category_id"]
            near_miss.near_miss_mscat_subcode_ids = serializer.validated_data["near_miss_mscat_subcode_ids"]
        near_miss.office_comment = office_comment or None
        near_miss.updated_by = actor_id
        near_miss.updated_date = timezone.now()
        if not supersede_to_incident:
            near_miss.state = Incident.State.OFFICE_COMMENTS_COMPLETED
        near_miss.save(update_fields=[
            "near_miss_priority",
            "near_miss_shell_tag",
            "near_miss_category_tags",
            "near_miss_mscat_category_id",
            "near_miss_mscat_subcode_id",
            "near_miss_mscat_subcode_ids",
            "office_comment",
            "state",
            "updated_by",
            "updated_date",
        ])

        superseded_incident = None
        if supersede_to_incident:
            try:
                superseded_incident = self.near_miss_supersede_service_class().supersede_near_miss(
                    near_miss.pk,
                    actor_id=actor_id,
                )
            except NearMissSupersedeError as exc:
                raise ValidationError(str(exc)) from exc
            near_miss.refresh_from_db()

        phase_log = IncidentPhaseLog.objects.create(
            incident=near_miss,
            phase_from=near_miss.current_phase,
            phase_to=near_miss.current_phase,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            loop_back_reason=decision_reason or f"Near-miss office comments accepted as {priority}.",
            actor_user_id=actor_id,
            actor_role_code=_normalized_role(request.user) or "OFFICE_REVIEWER",
            device_fingerprint=getattr(near_miss, "reporter_device_fingerprint", None),
            schema_version=near_miss.schema_version or 1,
        )
        record_field_changes(
            near_miss,
            old_state,
            user=request.user,
            field_names=tracked_fields,
            change_reason=decision_reason or f"Near-miss office comments accepted as {priority}.",
        )

        payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
        payload["suggested_priority"] = suggestion["priority"]
        payload["suggestion_rationale"] = suggestion["rationale"]
        payload["office_comments_phase_log"] = PhaseLogSerializer(phase_log).data
        payload["office_comment_phase_log"] = PhaseLogSerializer(phase_log).data
        payload["superseded_incident"] = (
            IncidentSerializer(superseded_incident, context={"request": request}).data
            if superseded_incident is not None
            else None
        )
        return Response(payload, status=status.HTTP_200_OK)
