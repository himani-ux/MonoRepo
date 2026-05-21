from __future__ import annotations

from rest_framework import generics
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission
from apps.safety.models import SCMMeeting
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers import SCMMeetingSerializer, SCMSignOffSerializer
from apps.safety.services.overdue_soi_blocker import OverdueSOIBlocker
from apps.safety.services.pdf_renderer import SCMLegacyPdfRenderer
from apps.safety.services.scm_state_machine import SCMStateMachine
from apps.safety.views.scm import SCMViewMixin, _normalized_role


class SCMSignOffMixin(SCMViewMixin):
    process_permission_class = HasProcessPermission.requiring("SAF_P_004")
    form_permission_class = HasFormPermission.requiring("SAF_F_003")
    blocker_class = OverdueSOIBlocker
    state_machine_class = SCMStateMachine
    pdf_renderer_class = SCMLegacyPdfRenderer

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method == "POST":
            permissions.append(self.process_permission_class())
        return permissions

    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_public_id_or_pk(queryset, self.kwargs["id"])

    def get_blocker(self) -> OverdueSOIBlocker:
        return self.blocker_class()

    def get_pdf_renderer(self) -> SCMLegacyPdfRenderer:
        return self.pdf_renderer_class()

    def _ensure_master_gate(self) -> None:
        if _normalized_role(getattr(self.request, "user", None)) != "MASTER":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "SCM sign-off is restricted to the Master in Step 3.6/3.7 (FEAT-SAF-SCM-004)."
            )

    def _build_preflight_payload(self, meeting: SCMMeeting) -> dict[str, object]:
        agenda_complete, agenda_errors = self.get_scm_repository().agenda_preflight_complete(meeting.id)
        overdue_soi_areas = self.get_blocker().check_overdue_soi(str(meeting.vessel_id))
        attendance_rows = self.get_scm_repository().list_attendance(meeting.id)
        has_attendance = attendance_rows.exists()
        has_attendance_warnings = attendance_rows.filter(
            wrh_data_available=False
        ).exists() or attendance_rows.filter(wrh_non_compliance_flag=True).exists()
        attendance_acknowledged = has_attendance and (
            not has_attendance_warnings or meeting.attendance_warnings_acknowledged_at is not None
        )
        signatures_complete, signature_errors, signature_summary = (
            self.get_scm_repository().signature_preflight_complete(meeting)
        )

        return {
            "meeting_id": meeting.id,
            "meeting_state": meeting.state,
            "overdue_soi_areas": overdue_soi_areas,
            "attendance_acknowledged": attendance_acknowledged,
            "agenda_complete": agenda_complete,
            "agenda_errors": agenda_errors,
            "attendance_warnings_present": has_attendance_warnings,
            "signatures_complete": signatures_complete,
            "signature_errors": signature_errors,
            "signature_summary": signature_summary,
        }


class SCMSignOffPreflightView(SCMSignOffMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        self._ensure_master_gate()
        return Response(self._build_preflight_payload(self.get_meeting()))


class SCMSignOffView(SCMSignOffMixin, generics.GenericAPIView):
    serializer_class = SCMSignOffSerializer

    def post(self, request, *args, **kwargs):
        self._ensure_master_gate()
        meeting = self.get_meeting()
        preflight = self._build_preflight_payload(meeting)
        overdue_messages = [item["message"] for item in preflight["overdue_soi_areas"]]
        errors: dict[str, object] = {}
        if overdue_messages:
            errors["soi_overdue"] = overdue_messages
        if not preflight["attendance_acknowledged"]:
            errors["attendance_acknowledged"] = ["Attendance must be recorded and WRH warnings acknowledged before sign-off."]
        if not preflight["agenda_complete"]:
            errors["agenda"] = preflight["agenda_errors"]
        if not preflight["signatures_complete"]:
            errors["signatures"] = preflight["signature_errors"]
        if meeting.state not in {SCMMeeting.State.SUBMITTED, SCMMeeting.State.REOPENED}:
            errors["state"] = [
                "SCM meeting must be finalized for Master sign-off before it can be signed off."
            ]
        if errors:
            return Response(
                {
                    "errors": errors,
                    "overdue_soi_areas": preflight["overdue_soi_areas"],
                },
                status=422,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        signature_payload = self.get_state_machine().sign_off(
            meeting,
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
            user=request.user,
        )

        pdf_result = self.get_pdf_renderer().render_scm_pdf(
            meeting_id=meeting.id,
            viewer_user=request.user,
            persist=True,
        )
        updated_meeting = self.get_scm_repository().read(meeting.id)
        response_serializer = SCMMeetingSerializer(updated_meeting, context=self.get_serializer_context())
        return Response(
            {
                **response_serializer.data,
                "signature": {
                    "typed_name": signature_payload.typed_name,
                    "device_fingerprint": signature_payload.device_fingerprint,
                    "signed_at": signature_payload.signed_at,
                },
                "pdf": {
                    "status": "generated",
                    "download_path": pdf_result.download_path,
                    "export_path": pdf_result.export_path,
                    "file_name": pdf_result.file_name,
                    "section_titles": pdf_result.section_titles,
                },
            },
            status=200,
        )
