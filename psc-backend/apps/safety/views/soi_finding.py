from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from django.utils.text import get_valid_filename
from rest_framework import generics, serializers
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasAnyProcessPermission, HasProcessPermission
from apps.safety.models import SOIFinding
from apps.safety.repositories import FindingRepository
from apps.safety.serializers import SOIFindingCreateSerializer, SOIFindingSerializer, SOIFindingSubmitSerializer
from apps.safety.services.high_severity_nudge import HighSeverityNudgeService
from apps.safety.services.high_severity_photo_validator import HighSeverityPhotoValidator
from apps.safety.services.life_threat_detector import LifeThreatDetector
from apps.safety.services.pdf_renderer import SOISummaryPdfRenderer
from apps.safety.services.repeat_finding_detector import RepeatFindingDetector
from apps.safety.views.soi import SOIViewMixin


class SOIFindingViewMixin(SOIViewMixin):
    finding_process_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_013", "SAF_P_002")
    finding_repository_class = FindingRepository
    high_severity_photo_validator_class = HighSeverityPhotoValidator
    high_severity_nudge_service_class = HighSeverityNudgeService
    life_threat_detector_class = LifeThreatDetector
    soi_summary_pdf_renderer_class = SOISummaryPdfRenderer
    repeat_finding_detector_class = RepeatFindingDetector

    def get_finding_repository(self) -> FindingRepository:
        return self.finding_repository_class()

    def get_high_severity_photo_validator(self) -> HighSeverityPhotoValidator:
        return self.high_severity_photo_validator_class()

    def get_high_severity_nudge_service(self) -> HighSeverityNudgeService:
        return self.high_severity_nudge_service_class()

    def get_life_threat_detector(self) -> LifeThreatDetector:
        return self.life_threat_detector_class()

    def get_soi_summary_pdf_renderer(self) -> SOISummaryPdfRenderer:
        return self.soi_summary_pdf_renderer_class()

    def get_repeat_finding_detector(self) -> RepeatFindingDetector:
        return self.repeat_finding_detector_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["finding_repository"] = self.get_finding_repository()
        context["high_severity_photo_validator"] = self.get_high_severity_photo_validator()
        context["high_severity_nudge_service"] = self.get_high_severity_nudge_service()
        context["life_threat_detector"] = self.get_life_threat_detector()
        context["repeat_finding_detector"] = self.get_repeat_finding_detector()
        context["actor_user"] = getattr(self.request, "user", None)
        return context


class SOIFindingListCreateView(SOIFindingViewMixin, generics.GenericAPIView):
    queryset = SOIFinding.objects.filter(is_deleted=False)

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method == "POST":
            permissions.append(self.finding_process_permission_class())
        return permissions

    def get(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        findings = self.get_finding_repository().list_for_inspection(inspection.id)
        serializer = SOIFindingSerializer(findings, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        self._ensure_safety_officer_gate(vessel_id=str(inspection.vessel_id))
        serializer = SOIFindingCreateSerializer(
            data=request.data,
            context={
                **self.get_serializer_context(),
                "inspection": inspection,
            },
        )
        serializer.is_valid(raise_exception=True)
        finding = serializer.save()
        response_serializer = SOIFindingSerializer(finding)
        payload = dict(response_serializer.data)
        nudge_result = getattr(serializer, "nudge_result", None)
        if nudge_result is not None:
            payload["high_severity_nudge"] = nudge_result.to_payload()
        return Response(payload, status=201)


class SOIFindingPhotoUploadView(SOIFindingViewMixin, generics.GenericAPIView):
    parser_classes = (MultiPartParser, FormParser)
    max_upload_bytes = 3 * 1024 * 1024
    allowed_content_types = {"image/jpeg", "image/jpg", "image/png"}
    allowed_suffixes = {".jpg", ".jpeg", ".png"}

    def get_permissions(self):
        return [self.form_permission_class(), self.finding_process_permission_class()]

    def post(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        self._ensure_safety_officer_gate(vessel_id=str(inspection.vessel_id))
        uploaded_file = request.FILES.get("photo") or request.FILES.get("file")
        if uploaded_file is None:
            raise serializers.ValidationError({"photo": "Select a photo to upload."})

        content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
        suffix = Path(str(uploaded_file.name or "")).suffix.lower()
        if content_type not in self.allowed_content_types or suffix not in self.allowed_suffixes:
            raise serializers.ValidationError({"photo": "Photo must be a JPG, JPEG, or PNG image."})

        size = int(getattr(uploaded_file, "size", 0) or 0)
        if size <= 0:
            raise serializers.ValidationError({"photo": "Photo file is empty."})
        if size > self.max_upload_bytes:
            raise serializers.ValidationError({"photo": "Photo must be 3MB or smaller."})

        relative_path, absolute_path = self._build_storage_path(
            vessel_id=str(inspection.vessel_id),
            inspection_id=int(inspection.id),
            original_name=str(uploaded_file.name or "photo"),
        )
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        with absolute_path.open("wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return Response(
            {
                "photo_attachment_path": relative_path,
                "file_name": Path(relative_path).name,
                "byte_size": size,
                "content_type": content_type,
            },
            status=201,
        )

    def _build_storage_path(self, *, vessel_id: str, inspection_id: int, original_name: str) -> tuple[str, Path]:
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        storage_root = Path(os.getenv("SAFETY_EXPORT_ROOT") or default_root).resolve(strict=False)
        suffix = Path(original_name).suffix.lower()
        safe_stem = Path(get_valid_filename(Path(original_name).stem or "photo")).stem[:80] or "photo"
        file_name = f"{safe_stem}-{uuid4().hex}{suffix}"
        safe_vessel_id = get_valid_filename(vessel_id or "unknown-vessel") or "unknown-vessel"
        relative_path = Path("vessels") / safe_vessel_id / "soi" / str(inspection_id) / "findings" / "photos" / file_name
        absolute_path = (storage_root / relative_path).resolve(strict=False)
        try:
            absolute_path.relative_to(storage_root)
        except ValueError as exc:
            raise serializers.ValidationError({"photo": "Invalid photo storage path."}) from exc
        return relative_path.as_posix(), absolute_path


class SOISubmitFindingsView(SOIFindingViewMixin, generics.GenericAPIView):
    serializer_class = SOIFindingSubmitSerializer

    def get_permissions(self):
        return [self.form_permission_class(), self.finding_process_permission_class()]

    def post(self, request, *args, **kwargs):
        inspection = self.get_inspection(kwargs["id"])
        self._ensure_safety_officer_gate(vessel_id=str(inspection.vessel_id))
        serializer = self.get_serializer(
            data=request.data,
            context={
                **self.get_serializer_context(),
                "inspection": inspection,
            },
        )
        serializer.is_valid(raise_exception=True)
        try:
            payload = serializer.save()
        except ValueError as exc:
            raise serializers.ValidationError({"submitted_area_ids": str(exc)}) from exc
        if payload.get("state") == "REPORTED":
            pdf_export = self.get_soi_summary_pdf_renderer().render_soi_pdf(
                inspection_id=inspection.id,
                viewer_user=request.user,
                persist=True,
            )
            payload["pdf_export"] = {
                "download_path": pdf_export.download_path,
                "export_path": pdf_export.export_path,
                "file_name": pdf_export.file_name,
            }
        return Response(payload)
