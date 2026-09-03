"""Audit finding capture API."""

import json
import os
import uuid

from django.conf import settings
from django.http import Http404
from django.core.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import AuditAttachment, AuditDetail
from apps.inspection.audit.permissions import (
    AUDIT_P_007,
    AUDIT_P_003,
    HasAnyAuditProcessPermission,
    request_has_audit_detail_process_id,
    user_can_access_audit_detail,
)
from apps.inspection.audit.serializers.finding import (
    AuditFindingCreateSerializer,
    AuditFindingResponseSerializer,
)
from apps.inspection.audit.services.finding import (
    AuditFindingStateError,
    AuditFindingValidationError,
    create_audit_finding,
)
from apps.inspection.audit.services.detail import get_audit_detail_by_id, get_audit_finding_by_id
from apps.inspection.audit.services.circular_link import (
    AuditCircularLinkValidationError,
    issue_circular_from_finding,
)


FINDING_EVIDENCE_FILE_FIELD = "evidence_files"
FINDING_EVIDENCE_CATEGORY = "FINDING_OBJECTIVE_EVIDENCE"
FINDING_EVIDENCE_MAX_BYTES = 20 * 1024 * 1024
FINDING_EVIDENCE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf", ".docx", ".xlsx"}


def _forbidden(message: str) -> Response:
    return Response(
        {
            "error": "FORBIDDEN",
            "message": message,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


class AuditFindingCreateView(APIView):
    """POST /api/audit/audits/{id}/findings/ for checklist and emergent findings."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            audit_detail = get_audit_detail_by_id(id)
        except (AuditDetail.DoesNotExist, ValueError) as exc:
            raise Http404("Audit not found.") from exc

        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")
        if not request_has_audit_detail_process_id(request, audit_detail, AUDIT_P_003):
            return _forbidden("You do not have permission to add findings for this audit.")

        try:
            payload = _finding_payload_without_files(request)
        except ValidationError as exc:
            return Response(
                {
                    "error": "AUDIT_FINDING_VALIDATION",
                    "message": _validation_message(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AuditFindingCreateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        evidence_files = list(request.FILES.getlist(FINDING_EVIDENCE_FILE_FIELD))
        try:
            for uploaded_file in evidence_files:
                _validate_finding_evidence_upload(uploaded_file)
        except AuditFindingValidationError as exc:
            return Response(
                {
                    "error": "AUDIT_FINDING_VALIDATION",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = create_audit_finding(
                audit_detail_id=audit_detail.id,
                created_by=_user_id(request.user),
                **serializer.validated_data,
            )
            _save_finding_evidence_files(
                audit_detail=audit_detail,
                finding=result.finding,
                files=evidence_files,
                uploaded_by=_user_id(request.user),
            )
        except AuditFindingStateError as exc:
            return Response(
                {
                    "error": "AUDIT_FINDING_STATE",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except AuditFindingValidationError as exc:
            return Response(
                {
                    "error": "AUDIT_FINDING_VALIDATION",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"data": AuditFindingResponseSerializer(result).data},
            status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
        )


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")


def _finding_payload_without_files(request) -> dict:
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
            payload[key] = clean_values[-1] if len(clean_values) == 1 else clean_values
    elif hasattr(data, "items"):
        payload = {
            key: value
            for key, value in data.items()
            if key not in file_keys and not _is_upload_value(value)
        }
    else:
        payload = {}

    if isinstance(payload.get("clauses"), str):
        try:
            payload["clauses"] = json.loads(payload["clauses"])
        except json.JSONDecodeError as exc:
            raise ValidationError({"clauses": "Clause references must be valid JSON."}) from exc

    return payload


def _is_upload_value(value) -> bool:
    return hasattr(value, "chunks") and hasattr(value, "name")


def _save_finding_evidence_files(*, audit_detail, finding, files, uploaded_by: str) -> None:
    for uploaded_file in files:
        _validate_finding_evidence_upload(uploaded_file)
        relative_path = _finding_evidence_relative_path(
            audit_detail_id=audit_detail.id,
            finding_id=finding.id,
            file_name=uploaded_file.name,
        )
        _save_uploaded_file(uploaded_file, relative_path)
        AuditAttachment.objects.create(
            audit_detail_id=audit_detail.id,
            audit_finding_id=finding.id,
            file_name=str(uploaded_file.name or "")[:255],
            file_path=relative_path,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type or "application/octet-stream",
            category=FINDING_EVIDENCE_CATEGORY,
            attachment_version="FINAL",
            uploaded_by=uploaded_by,
            description="Finding objective evidence",
        )


def _validate_finding_evidence_upload(uploaded_file) -> None:
    _, extension = os.path.splitext(str(uploaded_file.name or ""))
    if extension.lower() not in FINDING_EVIDENCE_EXTENSIONS:
        raise AuditFindingValidationError(
            "Attach evidence as an image, PDF, DOCX, or XLSX file."
        )
    if uploaded_file.size and uploaded_file.size > FINDING_EVIDENCE_MAX_BYTES:
        raise AuditFindingValidationError("Each evidence attachment must be 20 MB or smaller.")


def _finding_evidence_relative_path(*, audit_detail_id, finding_id, file_name: str) -> str:
    _, extension = os.path.splitext(str(file_name or ""))
    return "/".join(
        [
            "audit",
            "findings",
            str(audit_detail_id),
            str(finding_id),
            f"{uuid.uuid4()}{extension.lower()}",
        ]
    )


def _save_uploaded_file(uploaded_file, relative_path: str) -> None:
    media_root = os.path.abspath(os.fspath(getattr(settings, "MEDIA_ROOT", None) or os.path.join(os.getcwd(), "media")))
    full_path = os.path.abspath(os.path.join(media_root, relative_path.replace("/", os.sep)))
    try:
        stays_under_media_root = os.path.commonpath([media_root, full_path]) == media_root
    except ValueError:
        stays_under_media_root = False
    if not stays_under_media_root:
        raise AuditFindingValidationError("Invalid evidence attachment path.")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)


def _validation_message(exc: ValidationError) -> str:
    if hasattr(exc, "message_dict"):
        first_messages = next(iter(exc.message_dict.values()), [])
        if first_messages:
            return str(first_messages[0])
    messages = getattr(exc, "messages", None)
    if messages:
        return str(messages[0])
    return str(exc)


class AuditFindingIssueCircularView(APIView):
    """POST /api/audit/findings/{id}/issue-circular/ for fleet-wide NCs."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(AUDIT_P_007)]

    def post(self, request, id):
        from apps.inspection.audit.models import AuditFinding

        try:
            finding = get_audit_finding_by_id(id)
            audit_detail = get_audit_detail_by_id(finding.audit_detail_id)
        except (AuditFinding.DoesNotExist, AuditDetail.DoesNotExist) as exc:
            raise Http404("Finding not found.") from exc

        if not user_can_access_audit_detail(request.user, audit_detail):
            return _forbidden("You do not have access to this audit.")

        try:
            result = issue_circular_from_finding(finding_id=finding.id, user=request.user)
        except AuditCircularLinkValidationError as exc:
            return Response(
                {
                    "error": "AUDIT_CIRCULAR_LINK_VALIDATION",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "data": {
                    "status": result.status,
                    "circular_id": str(result.circular_id),
                    "detail_url": result.detail_url,
                    "payload": result.payload,
                }
            },
            status=status.HTTP_201_CREATED if result.status == "DRAFT_CREATED" else status.HTTP_200_OK,
        )
