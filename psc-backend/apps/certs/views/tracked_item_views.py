from __future__ import annotations

from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    TRACKED_ITEM_APPROVE_PROCESS_ID,
    TRACKED_ITEM_FORM_ID,
    TRACKED_ITEM_REJECT_PROCESS_ID,
    TRACKED_ITEM_SUBMIT_PROCESS_ID,
    TRACKED_ITEM_WRITE_PROCESS_ID,
    HasTrackedItemReadPermission,
    IsTrackedItemWriter,
    has_request_certs_perm,
    is_master_user,
    is_vessel_sub_officer,
    user_can_access_vessel,
)
from apps.certs.serializers.tracked_item import (
    TrackedItemWriteSerializer,
    serialize_approval_event,
    serialize_cert_change,
    serialize_pdf_blob,
    serialize_tracked_item,
    serialize_tracked_item_audit_event,
)
from apps.certs.services.audit_log import record_audit_event, resolve_actor_id
from apps.certs.services.approval_events import record_approval_event
from apps.certs.services.cert_change_log import record_cert_change_log
from apps.certs.services.ocr_pipeline import (
    OFFICE_CONTEXT,
    VESSEL_CONTEXT,
    OcrPipelineError,
    manual_entry_payload,
    process_cert_pdf,
)
from apps.certs.services.pdf_blob_repository import PdfBlobRepository, ocr_confidence_map
from apps.certs.services.pdf_blob_storage import save_uploaded_cert_pdf
from apps.certs.services.tracked_item_repository import TrackedItemRepository


repository = TrackedItemRepository()
pdf_repository = PdfBlobRepository()
ALL_RANKS_WITH_APPROVAL = "all_ranks_with_approval"
MASTER_ONLY = "master_only"
MAX_CERT_PDF_UPLOAD_BYTES = 50 * 1024 * 1024
AUTO_ACCEPTED_OCR_FIELDS = {
    "certificate_number": "certificateNumber",
    "issuing_authority": "issuingAuthority",
    "place_of_issue": "placeOfIssue",
    "issue_date": "issueDate",
    "expiry_date": "expiryDate",
}
OCR_DATE_FIELDS = {"issue_date", "expiry_date"}


class TrackedItemPermissionMixin:
    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), HasTrackedItemReadPermission()]
        return [IsAuthenticated(), IsTrackedItemWriter()]


class TrackedItemListCreateView(TrackedItemPermissionMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        page = repository.list_items(
            vessel_id=request.query_params.get("vesselId") or None,
            catalog_id=request.query_params.get("catalogId") or None,
            status_value=request.query_params.get("status") or None,
        )
        return Response(
            {
                "count": page.count,
                "results": [serialize_tracked_item(row) for row in page.results],
            }
        )

    def post(self, request, *args, **kwargs):
        serializer = TrackedItemWriteSerializer(data=request.data, context={"is_create": True})
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        reason = values.pop("reason", None)
        actor_id = resolve_actor_id(request.user)
        workflow_values, workflow_error = _initial_workflow_values(request.user, values)
        if workflow_error:
            return workflow_error
        values.update(workflow_values)
        with transaction.atomic():
            row = repository.create_item(values, actor_id=actor_id)
            serialized = serialize_tracked_item(row)
            record_audit_event(
                actor=request.user,
                action="create_tracked_item",
                entity_type="tracked_item",
                entity_id=serialized["id"],
                vessel_id=serialized["vesselId"],
                before=None,
                after=serialized,
                reason=reason or "Tracked item created.",
                metadata={"source": "api.certs.tracked_items"},
            )
            record_cert_change_log(
                tracked_item_id=serialized["id"],
                before=None,
                after=row,
                version_after=int(row.get("version") or 1),
                actor=request.user,
                source_ref="api.certs.tracked_items",
            )
        return Response(serialized, status=status.HTTP_201_CREATED)


class TrackedItemDetailView(TrackedItemPermissionMixin, generics.GenericAPIView):
    def get(self, request, tracked_item_id: str, *args, **kwargs):
        row = repository.get_item(str(tracked_item_id))
        if row is None:
            return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user_can_access_vessel(request.user, str(row.get("vessel_id"))):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        data = serialize_tracked_item(row)
        data.update(
            {
                "pdfVersions": [serialize_pdf_blob(blob) for blob in repository.list_pdf_versions(str(tracked_item_id))],
                "approvalEvents": [
                    serialize_approval_event(event) for event in repository.list_approval_events(str(tracked_item_id))
                ],
                "auditEvents": [
                    serialize_tracked_item_audit_event(event)
                    for event in repository.list_audit_events(str(tracked_item_id))
                ],
                "changeHistory": [
                    serialize_cert_change(change) for change in repository.list_change_history(str(tracked_item_id))
                ],
            }
        )
        return Response(data)

    def patch(self, request, tracked_item_id: str, *args, **kwargs):
        serializer = TrackedItemWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.pop("reason", None)
        with transaction.atomic():
            before, after = repository.update_item(
                str(tracked_item_id),
                serializer.validated_data,
                actor_id=resolve_actor_id(request.user),
            )
            if after is None:
                return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
            serialized_before = serialize_tracked_item(before) if before else None
            serialized_after = serialize_tracked_item(after)
            record_audit_event(
                actor=request.user,
                action="update_tracked_item",
                entity_type="tracked_item",
                entity_id=serialized_after["id"],
                vessel_id=serialized_after["vesselId"],
                before=serialized_before,
                after=serialized_after,
                reason=reason or "Tracked item updated.",
                metadata={"source": "api.certs.tracked_items"},
            )
            record_cert_change_log(
                tracked_item_id=serialized_after["id"],
                before=before,
                after=after,
                version_after=int(after.get("version") or 1),
                actor=request.user,
                source_ref="api.certs.tracked_items",
            )
        return Response(serialized_after)


class TrackedItemQuarantineResolveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsTrackedItemWriter]

    def post(self, request, tracked_item_id: str, *args, **kwargs):
        resolution = str(request.data.get("resolution") or "").strip()
        if resolution not in {"active", "expired"}:
            return Response(
                {"resolution": "Resolution must be either active or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason, reason_error = _required_reason(request.data.get("reason"))
        if reason_error:
            return reason_error

        current = repository.get_item(str(tracked_item_id))
        if current is None:
            return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
        if current.get("status") != "expired_at_onboarding":
            return Response(
                {"detail": "Only expired_at_onboarding rows can be resolved through this endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        values = {
            "status": "ok" if resolution == "active" else "expired",
            "lifecycleStatus": "active",
        }
        with transaction.atomic():
            before, after = repository.update_item(
                str(tracked_item_id),
                values,
                actor_id=resolve_actor_id(request.user),
            )
            if after is None:
                return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
            serialized_before = serialize_tracked_item(before) if before else None
            serialized_after = serialize_tracked_item(after)
            record_audit_event(
                actor=request.user,
                action="update_tracked_item",
                entity_type="tracked_item",
                entity_id=serialized_after["id"],
                vessel_id=serialized_after["vesselId"],
                before=serialized_before,
                after=serialized_after,
                reason=reason,
                metadata={
                    "source": "api.certs.tracked_items.quarantine_resolve",
                    "resolution": resolution,
                },
            )
            record_cert_change_log(
                tracked_item_id=serialized_after["id"],
                before=before,
                after=after,
                version_after=int(after.get("version") or 1),
                actor=request.user,
                source_ref="api.certs.tracked_items.quarantine_resolve",
            )
        return Response(serialized_after)


class TrackedItemUploadPdfView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasTrackedItemReadPermission]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, tracked_item_id: str, *args, **kwargs):
        if not has_request_certs_perm(request, TRACKED_ITEM_FORM_ID, TRACKED_ITEM_WRITE_PROCESS_ID):
            return Response({"detail": "You do not have access to upload Certs PDFs."}, status=status.HTTP_403_FORBIDDEN)

        uploaded_file = request.FILES.get("file")
        file_error = _validate_pdf_upload(uploaded_file)
        if file_error:
            return file_error

        current = repository.get_item(str(tracked_item_id))
        if current is None:
            return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str(current.get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        workflow_values, workflow_error = _upload_workflow_values(request.user, current)
        if workflow_error:
            return workflow_error

        context, context_error = _upload_ocr_context(request)
        if context_error:
            return context_error
        reason = str(request.data.get("reason") or "").strip() or "Certificate PDF uploaded."
        actor_id = resolve_actor_id(request.user)

        with transaction.atomic():
            stored = save_uploaded_cert_pdf(
                uploaded_file=uploaded_file,
                vessel_id=vessel_id,
                tracked_item_id=str(tracked_item_id),
            )
            blob = pdf_repository.create_blob_for_tracked_item(
                tracked_item_id=str(tracked_item_id),
                storage_path=str(stored["relative_path"]),
                filename=str(stored["filename"]),
                content_sha256=str(stored["sha256"]),
                content_size_bytes=int(stored["size"]),
                uploaded_by=actor_id,
            )
            blob_id = str(blob.get("blob_id"))
            try:
                ocr_payload = process_cert_pdf(str(stored["absolute_path"]), context=context)
            except OcrPipelineError as exc:
                ocr_payload = manual_entry_payload(
                    context=context,
                    engine_name="tesseract",
                    reason=str(exc),
                )
            processed_blob = pdf_repository.update_ocr_result(blob_id, ocr_payload)
            existing_blob_id = str(current.get("pdf_attachment_id") or "")
            if existing_blob_id:
                pdf_repository.mark_blob_superseded_for_retention(
                    blob_id=existing_blob_id,
                    section_code=current.get("catalog_section_code"),
                    is_class_tracked=bool(current.get("catalog_is_class_tracked")),
                    retain_all_versions=bool(current.get("catalog_retain_all_versions")),
                )
            update_values = {
                "pdfAttachmentId": blob_id,
                "pdfMissing": False,
                **_auto_accepted_tracked_item_values(ocr_payload),
                **workflow_values,
            }
            if str(current.get("status") or "") == "pending_first_upload":
                update_values["status"] = "ok"
            before, after = repository.update_item(str(tracked_item_id), update_values, actor_id=actor_id)
            if after is None:
                return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)

            serialized_before = serialize_tracked_item(before) if before else None
            serialized_after = serialize_tracked_item(after)
            serialized_blob = serialize_pdf_blob(processed_blob or blob)
            confidence_map = ocr_confidence_map(ocr_payload)
            record_audit_event(
                actor=request.user,
                action="upload_pdf",
                entity_type="pdf_blob",
                entity_id=blob_id,
                vessel_id=vessel_id,
                before=None,
                after=serialized_blob,
                reason=reason,
                metadata={
                    "source": "api.certs.tracked_items.upload_pdf",
                    "tracked_item_id": str(tracked_item_id),
                    "sha256": stored["sha256"],
                    "size": stored["size"],
                    "auto_applied_fields": sorted(set(update_values) - {"pdfAttachmentId", "pdfMissing", "status"}),
                },
            )
            record_audit_event(
                actor=request.user,
                action="ocr_processed",
                entity_type="pdf_blob",
                entity_id=blob_id,
                vessel_id=vessel_id,
                before=None,
                after=ocr_payload,
                reason="OCR confidence routing completed.",
                metadata={
                    "source": "api.certs.tracked_items.upload_pdf",
                    "tracked_item_id": str(tracked_item_id),
                    "context": context,
                    "status": ocr_payload.get("status"),
                    "confidence_per_field": confidence_map,
                },
            )
            record_cert_change_log(
                tracked_item_id=serialized_after["id"],
                before=before,
                after=after,
                version_after=int(after.get("version") or 1),
                actor=request.user,
                source_ref="api.certs.tracked_items.upload_pdf",
            )
            if workflow_values.get("approvalState") == "pending_master_approval":
                record_approval_event(
                    tracked_item_id=serialized_after["id"],
                    from_state=serialized_before.get("approvalState") if serialized_before else str(current.get("approval_state") or ""),
                    to_state="pending_master_approval",
                    actor=request.user,
                    reason=reason,
                )

        return Response(
            {
                "trackedItem": serialized_after,
                "pdfBlob": serialized_blob,
                "ocrPayload": ocr_payload,
                "ocrConfidencePerField": confidence_map,
            },
            status=status.HTTP_201_CREATED,
        )


class TrackedItemSubmitView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasTrackedItemReadPermission]

    def post(self, request, tracked_item_id: str, *args, **kwargs):
        if not has_request_certs_perm(request, TRACKED_ITEM_FORM_ID, TRACKED_ITEM_SUBMIT_PROCESS_ID):
            return Response({"detail": "You do not have access to submit Certs tracked items."}, status=status.HTTP_403_FORBIDDEN)
        reason, reason_error = _required_reason(request.data.get("reason"))
        if reason_error:
            return reason_error
        expected_version, version_error = _expected_version(request.data.get("version"))
        if version_error:
            return version_error

        current = repository.get_item(str(tracked_item_id))
        if current is None:
            return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user_can_access_vessel(request.user, str(current.get("vessel_id"))):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        approval_state = str(current.get("approval_state") or "")
        if approval_state == "rejected":
            if str(current.get("submitted_by") or "") != resolve_actor_id(request.user):
                return Response(
                    {"detail": "Only the original submitter may resubmit a rejected tracked item."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return _perform_transition(
                request=request,
                tracked_item_id=str(tracked_item_id),
                current=current,
                transition="resubmit_to_draft",
                action="submit_tracked_item",
                to_state="draft",
                reason=reason,
                expected_version=expected_version,
            )

        if approval_state != "draft":
            return Response({"detail": "Only draft tracked items can be submitted."}, status=status.HTTP_400_BAD_REQUEST)

        submission_scope = _catalog_submission_scope(current)
        if is_master_user(request.user):
            transition = "master_direct_approve"
            to_state = "approved"
        elif is_vessel_sub_officer(request.user):
            if submission_scope != ALL_RANKS_WITH_APPROVAL:
                return Response(
                    {"detail": "Only Master or office users may submit master_only rows."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            transition = "submit_for_master"
            to_state = "pending_master_approval"
        elif _is_office_direct_user(request.user):
            transition = "master_direct_approve"
            to_state = "approved"
        else:
            return Response({"detail": "Only Master or vessel sub-officers may submit through this endpoint."}, status=status.HTTP_403_FORBIDDEN)

        return _perform_transition(
            request=request,
            tracked_item_id=str(tracked_item_id),
            current=current,
            transition=transition,
            action="submit_tracked_item",
            to_state=to_state,
            reason=reason,
            expected_version=expected_version,
        )


class TrackedItemApproveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasTrackedItemReadPermission]

    def post(self, request, tracked_item_id: str, *args, **kwargs):
        if not has_request_certs_perm(request, TRACKED_ITEM_FORM_ID, TRACKED_ITEM_APPROVE_PROCESS_ID):
            return Response({"detail": "You do not have access to approve Certs tracked items."}, status=status.HTTP_403_FORBIDDEN)
        reason = str(request.data.get("reason") or "").strip() or "Tracked item approved."
        expected_version, version_error = _expected_version(request.data.get("version"))
        if version_error:
            return version_error

        current = repository.get_item(str(tracked_item_id))
        if current is None:
            return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _can_master_act_on_item(request.user, current):
            return Response({"detail": "Only the vessel Master may approve this tracked item."}, status=status.HTTP_403_FORBIDDEN)
        if current.get("approval_state") != "pending_master_approval":
            return Response({"detail": "Only pending Master approval rows can be approved."}, status=status.HTTP_400_BAD_REQUEST)

        return _perform_transition(
            request=request,
            tracked_item_id=str(tracked_item_id),
            current=current,
            transition="approve",
            action="approve_tracked_item",
            to_state="approved",
            reason=reason,
            expected_version=expected_version,
        )


class TrackedItemRejectView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasTrackedItemReadPermission]

    def post(self, request, tracked_item_id: str, *args, **kwargs):
        if not has_request_certs_perm(request, TRACKED_ITEM_FORM_ID, TRACKED_ITEM_REJECT_PROCESS_ID):
            return Response({"detail": "You do not have access to reject Certs tracked items."}, status=status.HTTP_403_FORBIDDEN)
        reason, reason_error = _required_reason(request.data.get("reason"))
        if reason_error:
            return reason_error
        expected_version, version_error = _expected_version(request.data.get("version"))
        if version_error:
            return version_error

        current = repository.get_item(str(tracked_item_id))
        if current is None:
            return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _can_master_act_on_item(request.user, current):
            return Response({"detail": "Only the vessel Master may reject this tracked item."}, status=status.HTTP_403_FORBIDDEN)
        if current.get("approval_state") != "pending_master_approval":
            return Response({"detail": "Only pending Master approval rows can be rejected."}, status=status.HTTP_400_BAD_REQUEST)

        return _perform_transition(
            request=request,
            tracked_item_id=str(tracked_item_id),
            current=current,
            transition="reject",
            action="reject_tracked_item",
            to_state="rejected",
            reason=reason,
            expected_version=expected_version,
        )


def _required_reason(value: object) -> tuple[str, Response | None]:
    reason = str(value or "").strip()
    if not reason:
        return "", Response({"reason": "Reason is required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(reason) < 10:
        return "", Response({"reason": "Reason must be at least 10 characters."}, status=status.HTTP_400_BAD_REQUEST)
    return reason, None


def _expected_version(value: object) -> tuple[int | None, Response | None]:
    if value in (None, ""):
        return None, None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, Response({"version": "Version must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
    if parsed < 1:
        return None, Response({"version": "Version must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)
    return parsed, None


def _validate_pdf_upload(uploaded_file) -> Response | None:
    if uploaded_file is None:
        return Response({"file": "Select a certificate PDF to upload."}, status=status.HTTP_400_BAD_REQUEST)
    filename = str(getattr(uploaded_file, "name", "") or "")
    content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix != "pdf" or content_type not in {"application/pdf", "application/x-pdf", ""}:
        return Response({"file": "Certificate upload must be a PDF file."}, status=status.HTTP_400_BAD_REQUEST)
    size = int(getattr(uploaded_file, "size", 0) or 0)
    if size <= 0:
        return Response({"file": "Certificate PDF is empty."}, status=status.HTTP_400_BAD_REQUEST)
    if size > MAX_CERT_PDF_UPLOAD_BYTES:
        return Response({"file": "Certificate PDF must be 50 MB or smaller."}, status=status.HTTP_400_BAD_REQUEST)
    return None


def _upload_ocr_context(request) -> tuple[str, Response | None]:
    requested_context = str(request.data.get("context") or "").strip().lower()
    if requested_context:
        if requested_context not in {OFFICE_CONTEXT, VESSEL_CONTEXT}:
            return "", Response({"context": "Context must be either office or vessel."}, status=status.HTTP_400_BAD_REQUEST)
        return requested_context, None
    if (getattr(request.user, "user_type", "") or "").upper() == "VESSEL":
        return VESSEL_CONTEXT, None
    return OFFICE_CONTEXT, None


def _upload_workflow_values(user, current: dict) -> tuple[dict, Response | None]:
    actor_id = resolve_actor_id(user)
    if is_vessel_sub_officer(user):
        if _catalog_submission_scope(current) != ALL_RANKS_WITH_APPROVAL:
            return {}, Response(
                {"detail": "Only Master or office users may upload PDFs for master_only rows."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return (
            {
                "approvalState": "pending_master_approval",
                "submittedBy": actor_id,
                "submittedAt": timezone.now(),
                "approvedBy": None,
                "approvedAt": None,
                "rejectionReason": None,
                "draftExpiresAt": None,
            },
            None,
        )
    if is_master_user(user) or _is_office_direct_user(user):
        return (
            {
                "approvalState": "approved",
                "submittedBy": actor_id,
                "submittedAt": timezone.now(),
                "approvedBy": actor_id,
                "approvedAt": timezone.now(),
                "rejectionReason": None,
                "draftExpiresAt": None,
            },
            None,
        )
    return {}, Response(
        {"detail": "Only Master, vessel sub-officers, or office users may upload Certs PDFs."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _auto_accepted_tracked_item_values(ocr_payload: dict) -> dict[str, str]:
    fields = ocr_payload.get("fields")
    if not isinstance(fields, dict):
        return {}

    values: dict[str, str] = {}
    for ocr_field, api_field in AUTO_ACCEPTED_OCR_FIELDS.items():
        payload = fields.get(ocr_field)
        if not isinstance(payload, dict):
            continue
        if payload.get("mode") != "auto_accept":
            continue
        value = payload.get("value")
        if value in (None, ""):
            continue
        text = str(value).strip()
        if not text:
            continue
        if ocr_field in OCR_DATE_FIELDS:
            parsed = _parse_ocr_date(text)
            if parsed is None:
                continue
            text = parsed
        values[api_field] = text
    return values


def _parse_ocr_date(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def _can_master_act_on_item(user, item: dict) -> bool:
    return is_master_user(user) and user_can_access_vessel(user, str(item.get("vessel_id")))


def _catalog_submission_scope(item: dict) -> str:
    return str(item.get("catalog_submission_scope") or item.get("submission_scope") or "").strip()


def _is_office_direct_user(user) -> bool:
    return (getattr(user, "user_type", "") or "").upper() != "VESSEL"


def _initial_workflow_values(user, values: dict) -> tuple[dict, Response | None]:
    actor_id = resolve_actor_id(user)
    now = timezone.now()
    catalog_id = values.get("catalogId")
    submission_scope = repository.get_catalog_submission_scope(str(catalog_id)) if catalog_id else None
    submission_scope = str(submission_scope or ALL_RANKS_WITH_APPROVAL)

    if is_master_user(user) or _is_office_direct_user(user):
        return (
            {
                "approvalState": "approved",
                "submittedBy": actor_id,
                "submittedAt": now,
                "approvedBy": actor_id,
                "approvedAt": now,
                "rejectionReason": None,
                "rejectionCount": 0,
                "draftExpiresAt": None,
            },
            None,
        )

    if is_vessel_sub_officer(user):
        if submission_scope != ALL_RANKS_WITH_APPROVAL:
            return {}, Response(
                {"detail": "Only Master or office users may create master_only tracked items."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return (
            {
                "approvalState": "draft",
                "submittedBy": actor_id,
                "submittedAt": None,
                "approvedBy": None,
                "approvedAt": None,
                "rejectionReason": None,
                "rejectionCount": 0,
                "draftExpiresAt": now + timedelta(days=7),
            },
            None,
        )

    return {}, Response(
        {"detail": "Only Master, vessel sub-officers, or office users may create tracked items."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _perform_transition(
    *,
    request,
    tracked_item_id: str,
    current: dict,
    transition: str,
    action: str,
    to_state: str,
    reason: str,
    expected_version: int | None,
):
    actor_id = resolve_actor_id(request.user)
    with transaction.atomic():
        before, after, updated = repository.transition_item(
            tracked_item_id,
            transition=transition,
            actor_id=actor_id,
            reason=reason,
            expected_version=expected_version,
        )
        if after is None:
            return Response({"detail": "Tracked item not found."}, status=status.HTTP_404_NOT_FOUND)
        if not updated:
            return Response(
                {"detail": "Tracked item was updated by another user. Refresh and retry."},
                status=status.HTTP_409_CONFLICT,
            )
        serialized_before = serialize_tracked_item(before or current)
        serialized_after = serialize_tracked_item(after)
        from_state = serialized_before.get("approvalState") or str(current.get("approval_state") or "")
        record_audit_event(
            actor=request.user,
            action=action,
            entity_type="tracked_item",
            entity_id=serialized_after["id"],
            vessel_id=serialized_after["vesselId"],
            before=serialized_before,
            after=serialized_after,
            reason=reason,
            metadata={"source": f"api.certs.tracked_items.{transition}"},
        )
        record_approval_event(
            tracked_item_id=serialized_after["id"],
            from_state=from_state,
            to_state=to_state,
            actor=request.user,
            reason=reason,
        )
        record_cert_change_log(
            tracked_item_id=serialized_after["id"],
            before=before,
            after=after,
            version_after=int(after.get("version") or 1),
            actor=request.user,
            source_ref=f"api.certs.tracked_items.{transition}",
        )
    return Response(serialized_after)
