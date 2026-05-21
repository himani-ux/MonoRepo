from __future__ import annotations

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasProcessPermission
from apps.safety.models import SCMMeeting, SCMSignature
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers import SCMSignatureSerializer
from apps.safety.views.scm import SCMViewMixin, _normalized_role


class SCMSignatureView(SCMViewMixin, generics.GenericAPIView):
    serializer_class = SCMSignatureSerializer

    def get_permissions(self):
        return [self.form_permission_class(), HasProcessPermission.requiring("SAF_P_002")()]

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_public_id_or_pk(queryset, self.kwargs["id"])

    def post(self, request, *args, **kwargs):
        meeting = self.get_meeting()
        self.get_state_machine().ensure_mutable(meeting)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signer_role = serializer.validated_data["signer_role"]
        current_role = _normalized_role(getattr(request, "user", None))
        if signer_role == SCMSignature.SignerRole.CO and current_role != "CO":
            raise PermissionDenied("CO signature is restricted to the Chief Officer.")
        if signer_role == SCMSignature.SignerRole.ATTENDEE and current_role not in {"CO", "MASTER"}:
            raise PermissionDenied("Attendee signature capture is restricted to CO or Master.")

        crew_id = str(serializer.validated_data["signer_crew_id"]).strip()
        display_name = crew_id
        attendance_row = self.get_scm_repository().list_attendance(meeting.id).filter(crew_id=crew_id).first()
        if signer_role == SCMSignature.SignerRole.ATTENDEE:
            if attendance_row is None or not attendance_row.present:
                return Response(
                    {"signer_crew_id": ["Attendee signature requires a present attendance row."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            display_name = attendance_row.display_name
        elif signer_role == SCMSignature.SignerRole.CO:
            expected_co_crew_id = self.get_scm_repository().resolve_regular_co_signature_crew_id(meeting)
            if crew_id != expected_co_crew_id:
                return Response(
                    {"signer_crew_id": ["CO signature must match the recorded Regular SCM Chief Officer."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            display_name = serializer.validated_data["typed_name"]

        payload = self.get_state_machine().validate_signature_payload(
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
        )
        signature = self.get_state_machine().record_signature(
            meeting,
            signer_role=signer_role,
            signer_crew_id=crew_id,
            display_name=display_name,
            typed_name=payload.typed_name,
            device_fingerprint=payload.device_fingerprint,
            signed_at=payload.signed_at,
            user=request.user,
        )
        return Response(
            {
                "id": signature.id,
                "public_id": str(signature.public_id),
                "meeting_id": signature.meeting_id,
                "signer_role": signature.signer_role,
                "signer_crew_id": signature.signer_crew_id,
                "display_name": signature.display_name,
                "typed_name": signature.typed_name,
                "signed_at": signature.signed_at,
            },
            status=status.HTTP_200_OK,
        )
