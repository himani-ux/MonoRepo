"""Audit registration API views."""

import os
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditDetail
from apps.inspection.audit.permissions import (
    AUDIT_P_001,
    AUDIT_P_003,
    AUDIT_P_013,
    HasAnyAuditProcessPermission,
    is_office_user,
    user_can_access_audit_detail,
)
from apps.inspection.audit.serializers.registration import (
    AuditRegistrationResponseSerializer,
    AuditRegistrationSerializer,
    RegisteredAuditListItemSerializer,
)
from apps.inspection.audit.services.vessels import audit_vessel_label_map


EXTERNAL_REPORT_FILE_FIELD = "external_report_file"
REPEATED_FORM_FIELDS = {
    "standards",
    "external_audit_subtypes",
    "linked_cert_ids",
    "team_members",
    "attendees",
    "schedule_blocks",
}


def _is_pdf_upload(uploaded_file) -> bool:
    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    file_name = (getattr(uploaded_file, "name", "") or "").lower()
    return content_type == "application/pdf" or file_name.endswith(".pdf")


def _clean_path_part(value) -> str:
    cleaned = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in str(value or "unknown"))
    return cleaned.strip("-") or "unknown"


def _external_report_relative_path(vessel_id) -> str:
    return "/".join(
        [
            "audit",
            "external",
            _clean_path_part(vessel_id),
            f"{uuid.uuid4()}.pdf",
        ]
    )


def _audit_media_root() -> str:
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_root:
        return os.fspath(media_root)
    return os.path.join(os.getcwd(), "media")


def _external_report_full_path(relative_path: str) -> str:
    media_root = os.path.abspath(_audit_media_root())
    full_path = os.path.abspath(os.path.join(media_root, relative_path.replace("/", os.sep)))
    try:
        stays_under_media_root = os.path.commonpath([media_root, full_path]) == media_root
    except ValueError:
        stays_under_media_root = False
    if not stays_under_media_root:
        raise ValidationError({EXTERNAL_REPORT_FILE_FIELD: "Invalid external audit report path."})
    return full_path


def _save_external_report_file(uploaded_file, relative_path: str) -> str:
    full_path = _external_report_full_path(relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return full_path


def _remove_saved_external_report(full_path: str | None) -> None:
    if not full_path:
        return
    try:
        os.remove(full_path)
    except FileNotFoundError:
        return


def _is_upload_value(value) -> bool:
    return hasattr(value, "chunks") and hasattr(value, "name")


def _request_payload_without_files(request) -> dict:
    data = request.data
    file_keys = set(request.FILES.keys())

    if hasattr(data, "lists"):
        payload = {}
        for key, values in data.lists():
            if key in file_keys:
                continue
            clean_values = [value for value in values if not _is_upload_value(value)]
            if not clean_values:
                continue
            if key in REPEATED_FORM_FIELDS:
                payload[key] = clean_values
            else:
                payload[key] = clean_values[-1] if len(clean_values) == 1 else clean_values
        return payload

    if hasattr(data, "items"):
        return {
            key: value
            for key, value in data.items()
            if key not in file_keys and not _is_upload_value(value)
        }

    return {}


def _prepare_external_report_upload(payload, request):
    uploaded_file = request.FILES.get(EXTERNAL_REPORT_FILE_FIELD)
    if not uploaded_file:
        return None

    if not _is_pdf_upload(uploaded_file):
        raise ValidationError({EXTERNAL_REPORT_FILE_FIELD: "Attach a PDF file."})

    relative_path = _external_report_relative_path(payload.get("vessel_id"))
    payload["external_report_file_name"] = uploaded_file.name
    payload["external_report_file_path"] = relative_path
    payload["external_report_mime_type"] = uploaded_file.content_type or "application/pdf"
    payload["external_report_file_size"] = uploaded_file.size
    return uploaded_file, relative_path


class AuditRegistrationView(APIView):
    """GET/POST /api/audit/audits/ registered-audit list and registration endpoint."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [
        IsAuthenticated,
        HasAnyAuditProcessPermission.requiring_any(AUDIT_P_001, AUDIT_P_003, AUDIT_P_013),
    ]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return super().get_permissions()

    def get(self, request):
        audit_rows = [
            audit_detail
            for audit_detail in AuditDetail.objects.order_by("-created_date", "-id")
            if user_can_access_audit_detail(request.user, audit_detail)
        ]
        serializer = RegisteredAuditListItemSerializer(
            audit_rows,
            many=True,
            context={"vessel_label_map": audit_vessel_label_map([row.vessel_id for row in audit_rows])},
        )
        return Response({"data": {"count": len(audit_rows), "results": serializer.data}})

    def post(self, request):
        payload = _request_payload_without_files(request)
        is_external = payload.get("audit_classification") == "EXTERNAL"
        if not is_external and not is_office_user(request.user):
            return Response(
                {
                    "error": "FORBIDDEN",
                    "message": "Audit registration is restricted to office users.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        prepared_upload = _prepare_external_report_upload(payload, request) if is_external else None
        serializer = AuditRegistrationSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        saved_full_path = None
        try:
            if prepared_upload:
                uploaded_file, relative_path = prepared_upload
                saved_full_path = _save_external_report_file(uploaded_file, relative_path)
            result = serializer.save()
        except Exception:
            _remove_saved_external_report(saved_full_path)
            raise

        response_serializer = AuditRegistrationResponseSerializer(result)
        return Response(
            {
                "data": response_serializer.data,
                "message": "Audit registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )
