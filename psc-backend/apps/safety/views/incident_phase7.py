from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers.incident_phase7 import (
    IncidentPhase7AcceptSerializer,
    IncidentPhase7SendBackSerializer,
    build_phase7_preflight_payload,
)
from apps.safety.tasks.pdf_generation_task import generate_incident_pdf_export
from apps.safety.services.field_history_recorder import capture_model_state, record_field_changes, resolve_actor_id
from apps.safety.services.phase_state_machine import PhaseStateMachine
from apps.safety.services.signature_chain import SignatureChainService
from apps.safety.views.incident import IncidentViewMixin, _normalized_role


FM_ROLE_CODES = {"FM", "FLEET MANAGER"}
DPA_ROLE_CODES = {"DPA"}
HOD_ROLE_CODES = {"HOD", "HEAD OF DEPARTMENT", "CE", "CHIEF ENGINEER", "CO", "CHIEF OFFICER"}
GREEN_BAND_PIC_ROLE_CODES = {
    "PIC",
    "VESSEL SUPERINTENDENT",
    "OFFICE_PIC",
    "OFFICE_SSQE",
    "OFFICE_SUPT",
}


class IncidentPhase7ViewMixin(IncidentViewMixin):
    incident_lookup_url_kwarg = "id"
    signature_chain_service_class = SignatureChainService
    phase_state_machine_class = PhaseStateMachine

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_incident(self) -> Incident:
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        return get_by_public_id_or_pk(queryset, self.kwargs[self.incident_lookup_url_kwarg])

    def get_object(self):
        return self.get_incident()

    def get_signature_chain(self) -> SignatureChainService:
        return self.signature_chain_service_class()

    def get_phase_state_machine(self) -> PhaseStateMachine:
        return self.phase_state_machine_class()

    def _require_phase_seven(self, incident: Incident) -> None:
        if incident.current_phase != 7:
            raise ValidationError("Phase 7 actions require current_phase = 7.")

    def _require_process_permission(self, process_id: str) -> None:
        permission = HasProcessPermission.requiring(process_id)()
        if not permission.has_permission(self.request, self):
            raise PermissionDenied("You do not have permission to perform this Phase 7 action.")

    def _enforce_band_actor(self, incident: Incident, *, action: str) -> str:
        role = _normalized_role(self.request.user)
        actor_id = resolve_actor_id(self.request.user)
        actor_id_normalized = actor_id.strip().upper()
        if incident.risk_band == Incident.RiskBand.GREEN:
            assigned_pic = (incident.pic_user_id or "").strip().upper()
            is_role_based_pic = assigned_pic in GREEN_BAND_PIC_ROLE_CODES
            if actor_id_normalized != assigned_pic and not (
                is_role_based_pic and role in GREEN_BAND_PIC_ROLE_CODES
            ):
                raise PermissionDenied("GREEN-band Phase 7 actions are restricted to the assigned PIC.")
            return SignatureChainService.PIC
        if incident.risk_band == Incident.RiskBand.YELLOW:
            if role not in DPA_ROLE_CODES:
                raise PermissionDenied("YELLOW-band Phase 7 actions are restricted to DPA.")
            return SignatureChainService.DPA
        if incident.risk_band == Incident.RiskBand.RED:
            if action == "approve-red":
                if role not in FM_ROLE_CODES:
                    raise PermissionDenied("RED-band final approval is restricted to FM.")
                return SignatureChainService.FM
            if role not in DPA_ROLE_CODES:
                raise PermissionDenied("RED-band DPA acceptance is restricted to DPA.")
            return SignatureChainService.DPA
        raise ValidationError("Incident risk band must be assigned before Phase 7 actions.")


class IncidentPhase7PreflightView(IncidentPhase7ViewMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        incident = self.get_incident()
        return Response(build_phase7_preflight_payload(incident), status=status.HTTP_200_OK)


class IncidentPhase7AcceptView(IncidentPhase7ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentPhase7AcceptSerializer

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._require_phase_seven(incident)
        role_code = self._enforce_band_actor(incident, action="accept")
        self._require_process_permission(
            "SAF_P_004" if incident.risk_band in {Incident.RiskBand.YELLOW, Incident.RiskBand.RED} else "SAF_P_006"
        )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signature_chain = self.get_signature_chain()
        blockers = signature_chain.phase_seven_blockers(incident, action_role=role_code)
        if blockers:
            raise ValidationError({"blockers": sorted(set(blockers))})

        old_state = capture_model_state(incident, field_names=("dpa_accepted_at", "dpa_accepted_by"))
        signature_payload = signature_chain.stamp_phase7_signature(
            incident,
            role_code=role_code,
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
            user=request.user,
        )
        record_field_changes(
            incident,
            old_state,
            user=request.user,
            field_names=("dpa_accepted_at", "dpa_accepted_by"),
            change_reason="Phase 7 acceptance signature captured.",
        )

        if incident.risk_band == Incident.RiskBand.RED:
            preflight = build_phase7_preflight_payload(incident)
            return Response(
                {
                    "state": "PHASE_7_DPA_ACCEPTED",
                    "current_phase": incident.current_phase,
                    "dpa_accepted_at": incident.dpa_accepted_at,
                    "dpa_accepted_by": incident.dpa_accepted_by,
                    "requires_fm_approval": True,
                    "signature": {
                        "typed_name": signature_payload.typed_name,
                        "device_fingerprint": signature_payload.device_fingerprint,
                        "signed_at": signature_payload.signed_at,
                    },
                    "preflight": preflight,
                },
                status=status.HTTP_200_OK,
            )

        incident.state = "APPROVED"
        incident.updated_by = resolve_actor_id(request.user)
        incident.updated_date = timezone.now()
        incident.save(update_fields=["state", "updated_by", "updated_date"])

        transition = self.get_phase_state_machine().transition(incident.pk, 8, request.user)
        incident.refresh_from_db()
        pdf_export = generate_incident_pdf_export(incident_id=incident.pk, viewer_user=request.user)
        return Response(
            {
                "state": incident.state,
                "current_phase": incident.current_phase,
                "dpa_accepted_at": incident.dpa_accepted_at,
                "dpa_accepted_by": incident.dpa_accepted_by,
                "transition": transition,
                "pdf_export": {
                    "download_path": pdf_export.download_path,
                    "export_path": pdf_export.export_path,
                    "file_name": pdf_export.file_name,
                },
                "pdf_preview": build_phase7_preflight_payload(incident)["pdf_preview"],
            },
            status=status.HTTP_200_OK,
        )


class IncidentPhase7HodSignatureView(IncidentPhase7ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentPhase7AcceptSerializer

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._require_phase_seven(incident)
        role = _normalized_role(request.user)
        if role not in HOD_ROLE_CODES:
            raise PermissionDenied("Phase 7 HOD signature is restricted to the department HOD.")

        signature_chain = self.get_signature_chain()
        if signature_chain.signature_status(incident)["hod"]["present"]:
            raise ValidationError("HOD signature is already recorded for this incident.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signature_payload = signature_chain.stamp_phase7_supporting_signature(
            incident,
            role_code=SignatureChainService.HOD,
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
            user=request.user,
        )
        incident.refresh_from_db()
        return Response(
            {
                "state": incident.state,
                "current_phase": incident.current_phase,
                "signature": {
                    "typed_name": signature_payload.typed_name,
                    "device_fingerprint": signature_payload.device_fingerprint,
                    "signed_at": signature_payload.signed_at,
                },
                "preflight": build_phase7_preflight_payload(incident),
            },
            status=status.HTTP_200_OK,
        )


class IncidentPhase7ApproveRedView(IncidentPhase7ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentPhase7AcceptSerializer

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._require_phase_seven(incident)
        if incident.risk_band != Incident.RiskBand.RED:
            raise ValidationError("RED approval is only valid for RED-band incidents.")
        role_code = self._enforce_band_actor(incident, action="approve-red")
        self._require_process_permission("SAF_P_005")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signature_chain = self.get_signature_chain()
        blockers = signature_chain.phase_seven_blockers(incident, action_role=role_code)
        if blockers:
            raise ValidationError({"blockers": sorted(set(blockers))})

        old_state = capture_model_state(incident, field_names=("fm_approved_at", "fm_approved_by"))
        signature_chain.stamp_phase7_signature(
            incident,
            role_code=role_code,
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
            user=request.user,
        )
        record_field_changes(
            incident,
            old_state,
            user=request.user,
            field_names=("fm_approved_at", "fm_approved_by"),
            change_reason="Phase 7 RED-band FM signature captured.",
        )

        incident.state = "APPROVED"
        incident.updated_by = resolve_actor_id(request.user)
        incident.updated_date = timezone.now()
        incident.save(update_fields=["state", "updated_by", "updated_date"])

        transition = self.get_phase_state_machine().transition(incident.pk, 8, request.user)
        incident.refresh_from_db()
        pdf_export = generate_incident_pdf_export(incident_id=incident.pk, viewer_user=request.user)
        return Response(
            {
                "state": incident.state,
                "current_phase": incident.current_phase,
                "dpa_accepted_at": incident.dpa_accepted_at,
                "dpa_accepted_by": incident.dpa_accepted_by,
                "fm_approved_at": incident.fm_approved_at,
                "fm_approved_by": incident.fm_approved_by,
                "transition": transition,
                "pdf_export": {
                    "download_path": pdf_export.download_path,
                    "export_path": pdf_export.export_path,
                    "file_name": pdf_export.file_name,
                },
                "pdf_preview": build_phase7_preflight_payload(incident)["pdf_preview"],
            },
            status=status.HTTP_200_OK,
        )


class IncidentPhase7SendBackView(IncidentPhase7ViewMixin, generics.GenericAPIView):
    serializer_class = IncidentPhase7SendBackSerializer

    def post(self, request, *args, **kwargs):
        incident = self.get_incident()
        self._require_phase_seven(incident)
        self._enforce_band_actor(incident, action="accept")
        self._require_process_permission("SAF_P_003")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_phase = serializer.validated_data["target_phase"]
        reason = serializer.validated_data["reason"]
        old_state = capture_model_state(incident, field_names=("current_phase", "state"))

        incident.current_phase = target_phase
        incident.state = "SENT_BACK"
        incident.updated_by = resolve_actor_id(request.user)
        incident.updated_date = timezone.now()
        incident.save(update_fields=["current_phase", "state", "updated_by", "updated_date"])

        record_field_changes(
            incident,
            old_state,
            user=request.user,
            field_names=("current_phase", "state"),
            change_reason=reason,
        )
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=7,
            phase_to=target_phase,
            transition_type=IncidentPhaseLog.TransitionType.REWORK,
            loop_back_reason=reason,
            actor_user_id=resolve_actor_id(request.user),
            actor_role_code=_normalized_role(request.user) or "SYSTEM",
            device_fingerprint=incident.reporter_device_fingerprint,
            schema_version=incident.schema_version or 1,
        )

        return Response(
            {
                "state": incident.state,
                "current_phase": incident.current_phase,
                "target_phase": target_phase,
                "reason": reason,
            },
            status=status.HTTP_200_OK,
        )
