from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasAnyProcessPermission
from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers import NearMissSerializer, PhaseLogSerializer
from apps.safety.services import NotificationWriter, capture_model_state, record_field_changes
from apps.safety.services.signature_chain import SignatureChainService
from apps.safety.views.near_miss import NearMissViewMixin, _normalized_role, _resolve_actor_id


VESSEL_REVIEW_ROLES = {
    "MASTER",
    "CAPTAIN",
    "CO",
    "CE",
    "HOD",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "HEAD OF DEPARTMENT",
}


class NearMissReviewActionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=("SUBMIT_TO_OFFICE", "SEND_BACK"))
    comment = serializers.CharField(allow_blank=True, required=False, trim_whitespace=True)
    typed_name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    device_fingerprint = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def validate(self, attrs):
        decision = str(attrs["decision"]).strip().upper()
        comment = str(attrs.get("comment") or "").strip()
        if decision == "SEND_BACK" and not comment:
            raise serializers.ValidationError({"comment": "Rework requires reviewer comments."})
        attrs["decision"] = decision
        attrs["comment"] = comment
        return attrs


class NearMissReworkSubmitSerializer(serializers.Serializer):
    comment = serializers.CharField(allow_blank=False, trim_whitespace=True)


class NearMissReviewView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissReviewActionSerializer
    review_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_002", "SAF_P_006")
    notification_writer_class = NotificationWriter
    signature_service_class = SignatureChainService

    def get_permissions(self):
        return [self.form_permission_class(), self.review_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_notification_writer(self) -> NotificationWriter:
        return self.notification_writer_class()

    def get_signature_service(self) -> SignatureChainService:
        return self.signature_service_class()

    def get_near_miss(self) -> Incident:
        near_miss = get_by_public_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Vessel review is only available for near-miss records.")
        if near_miss.state in {Incident.State.CLOSED, Incident.State.SUPERSEDED}:
            raise ValidationError("Closed or superseded near misses cannot be reviewed.")
        return near_miss

    def _enforce_vessel_reviewer_role(self) -> None:
        if _normalized_role(self.request.user) not in VESSEL_REVIEW_ROLES:
            raise PermissionDenied("Near-miss vessel review is restricted to Master, HOD, CO, or CE.")

    def post(self, request, *args, **kwargs):
        near_miss = self.get_near_miss()
        self._enforce_vessel_reviewer_role()
        if near_miss.state != Incident.State.PENDING_VESSEL_REVIEW:
            raise ValidationError("Near miss is not awaiting vessel-side review.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor_id = _resolve_actor_id(request.user)
        actor_role = _normalized_role(request.user) or "VESSEL_REVIEWER"
        decision = serializer.validated_data["decision"]
        comment = serializer.validated_data["comment"]
        signature = self.get_signature_service().validate_payload(
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
        )
        next_state = (
            Incident.State.READY_FOR_DPA_TRIAGE
            if decision == "SUBMIT_TO_OFFICE"
            else Incident.State.REWORK_REQUIRED
        )
        old_state = capture_model_state(
            near_miss,
            field_names=("state", "updated_by", "updated_date"),
        )
        near_miss.state = next_state
        near_miss.updated_by = actor_id
        near_miss.updated_date = timezone.now()
        near_miss.save(update_fields=("state", "updated_by", "updated_date"))
        record_field_changes(
            near_miss,
            old_state,
            user=request.user,
            field_names=("state", "updated_by", "updated_date"),
            change_reason=comment or f"Near-miss vessel review decision: {decision}.",
        )
        phase_log = IncidentPhaseLog.objects.create(
            incident=near_miss,
            phase_from=near_miss.current_phase,
            phase_to=near_miss.current_phase,
            transition_type=(
                IncidentPhaseLog.TransitionType.REWORK
                if decision == "SEND_BACK"
                else IncidentPhaseLog.TransitionType.FORWARD
            ),
            loop_back_reason=comment or f"Near-miss vessel review decision: {decision}.",
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            device_fingerprint=signature.device_fingerprint,
            signature_valid=True,
            schema_version=near_miss.schema_version or 1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name="near_miss_vessel_review_signature",
            old_value=None,
            new_value={
                "typed_name": signature.typed_name,
                "signed_at": signature.signed_at.isoformat(),
                "device_fingerprint": signature.device_fingerprint,
                "signed_by": actor_id,
                "signed_role": actor_role,
                "decision": decision,
            },
            change_reason=comment or f"Near-miss vessel review decision: {decision}.",
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            schema_version=near_miss.schema_version or 1,
        )
        if decision == "SEND_BACK":
            self.get_notification_writer().dispatch_notification(
                record_id=near_miss.pk,
                recipients=["MASTER"],
                kind="NEAR_MISS_REWORK_REQUIRED",
                title="Near miss sent back for rework",
                message=comment,
                payload={"near_miss_id": near_miss.pk, "state": near_miss.state},
                send_slack=True,
            )
        else:
            self.get_notification_writer().dispatch_notification(
                record_id=near_miss.pk,
                recipients=["DPA", "PIC", "SAFETY_CHANNEL"],
                kind="NEAR_MISS_READY_FOR_DPA_TRIAGE",
                title="Near miss ready for DPA triage",
                message=f"Near miss {near_miss.incident_number} completed vessel review.",
                payload={"near_miss_id": near_miss.pk, "state": near_miss.state},
                send_slack=True,
            )

        payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
        payload["review_phase_log"] = PhaseLogSerializer(phase_log).data
        payload["review_signature"] = {
            "typed_name": signature.typed_name,
            "signed_at": signature.signed_at,
            "device_fingerprint": signature.device_fingerprint,
            "signed_by": actor_id,
            "signed_role": actor_role,
        }
        return Response(payload, status=status.HTTP_200_OK)


class NearMissReworkSubmitView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissReworkSubmitSerializer
    rework_permission_class = NearMissViewMixin.process_permission_class.requiring("SAF_P_001")

    def get_permissions(self):
        return [self.form_permission_class(), self.rework_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def post(self, request, *args, **kwargs):
        near_miss = get_by_public_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Rework is only available for near-miss records.")
        if near_miss.state != Incident.State.REWORK_REQUIRED:
            raise ValidationError("Near miss is not awaiting reporter rework.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor_id = _resolve_actor_id(request.user)
        actor_role = _normalized_role(request.user) or "REPORTER"
        old_state = capture_model_state(
            near_miss,
            field_names=("state", "updated_by", "updated_date"),
        )
        near_miss.state = Incident.State.PENDING_VESSEL_REVIEW
        near_miss.updated_by = actor_id
        near_miss.updated_date = timezone.now()
        near_miss.save(update_fields=("state", "updated_by", "updated_date"))
        record_field_changes(
            near_miss,
            old_state,
            user=request.user,
            field_names=("state", "updated_by", "updated_date"),
            change_reason=serializer.validated_data["comment"],
        )
        phase_log = IncidentPhaseLog.objects.create(
            incident=near_miss,
            phase_from=near_miss.current_phase,
            phase_to=near_miss.current_phase,
            transition_type=IncidentPhaseLog.TransitionType.REWORK,
            loop_back_reason=serializer.validated_data["comment"],
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            device_fingerprint=getattr(near_miss, "reporter_device_fingerprint", None),
            schema_version=near_miss.schema_version or 1,
        )
        payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
        payload["rework_phase_log"] = PhaseLogSerializer(phase_log).data
        return Response(payload, status=status.HTTP_200_OK)
