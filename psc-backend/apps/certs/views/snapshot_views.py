from __future__ import annotations

from django.core.exceptions import SuspiciousFileOperation
from django.db import transaction
from django.http import FileResponse
from django.utils.text import get_valid_filename
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    RECONCILIATION_FORM_ID,
    RECONCILIATION_UPLOAD_PROCESS_ID,
    TRACKED_ITEM_FORM_ID,
    HasReconciliationReadPermission,
    has_request_certs_perm,
    is_reconciliation_uploader,
    user_can_access_vessel,
)
from apps.certs.jobs.parser_worker import run_class_snapshot_parser
from apps.certs.serializers.snapshot import (
    ClassSnapshotUploadSerializer,
    serialize_class_snapshot,
    serialize_reconciliation_run,
)
from apps.certs.services.audit_log import record_audit_event, resolve_actor_id
from apps.certs.services.pdf_blob_repository import PdfBlobRepository
from apps.certs.services.pdf_blob_storage import resolve_pdf_blob_path, save_uploaded_class_snapshot_pdf
from apps.certs.services.snapshot_repository import ClassSnapshotRepository


repository = ClassSnapshotRepository()
pdf_repository = PdfBlobRepository()
MAX_CLASS_SNAPSHOT_UPLOAD_BYTES = 50 * 1024 * 1024


class HasClassSnapshotPdfReadPermission(BasePermission):
    message = "You do not have access to this class status PDF."

    def has_permission(self, request, view) -> bool:
        return has_request_certs_perm(request, RECONCILIATION_FORM_ID) or has_request_certs_perm(request, TRACKED_ITEM_FORM_ID)


class ClassSnapshotListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        page = repository.list_snapshots(
            vessel_id=request.query_params.get("vesselId") or None,
            class_society=request.query_params.get("classSociety") or None,
            parse_status=request.query_params.get("parseStatus") or None,
            page=int(request.query_params.get("page") or 1),
            page_size=int(request.query_params.get("pageSize") or 25),
        )
        return Response(
            {
                "count": page["count"],
                "results": [serialize_class_snapshot(row) for row in page["results"]],
            }
        )

    def post(self, request, *args, **kwargs):
        if not has_request_certs_perm(request, RECONCILIATION_FORM_ID, RECONCILIATION_UPLOAD_PROCESS_ID):
            return Response({"detail": "You do not have access to upload class snapshots."}, status=status.HTTP_403_FORBIDDEN)
        if not is_reconciliation_uploader(request.user):
            return Response({"detail": "Only office users may upload class snapshots."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClassSnapshotUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vessel_id = str(serializer.validated_data["vesselId"])
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        uploaded_file = request.FILES.get("file")
        file_error = _validate_pdf_upload(uploaded_file)
        if file_error:
            return file_error
        actor_id = resolve_actor_id(request.user)

        with transaction.atomic():
            stored = save_uploaded_class_snapshot_pdf(uploaded_file=uploaded_file, vessel_id=vessel_id)
            blob = pdf_repository.create_snapshot_blob(
                storage_path=str(stored["relative_path"]),
                filename=str(stored["filename"]),
                content_sha256=str(stored["sha256"]),
                content_size_bytes=int(stored["size"]),
                uploaded_by=actor_id,
            )
            snapshot = repository.create_snapshot(
                vessel_id=vessel_id,
                class_society=str(serializer.validated_data["classSociety"]),
                pdf_blob_id=str(blob["blob_id"]),
                printed_on_date=serializer.validated_data.get("printedOnDate"),
                uploaded_by=actor_id,
                upload_sha256=str(stored["sha256"]),
            )
            parsed_snapshot, _run = run_class_snapshot_parser(str(snapshot["snapshot_id"]), repository=repository)
            if parsed_snapshot is not None:
                snapshot = parsed_snapshot
            serialized = serialize_class_snapshot(snapshot)
            record_audit_event(
                actor=request.user,
                action="upload_class_snapshot",
                entity_type="class_status_snapshot",
                entity_id=serialized["id"],
                vessel_id=serialized["vesselId"],
                before=None,
                after=serialized,
                reason="Class status snapshot uploaded.",
                metadata={
                    "source": "api.certs.class_snapshots",
                    "sha256": stored["sha256"],
                    "size": stored["size"],
                    "class_society": serialized["classSociety"],
                },
            )
        return Response(serialized, status=status.HTTP_201_CREATED)


class ClassSnapshotDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def get(self, request, snapshot_id: str, *args, **kwargs):
        snapshot = repository.get_snapshot(str(snapshot_id))
        if snapshot is None:
            return Response({"detail": "Class snapshot not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user_can_access_vessel(request.user, str(snapshot.get("vessel_id"))):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        return Response(serialize_class_snapshot(snapshot))


class ClassSnapshotPdfInlineView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasClassSnapshotPdfReadPermission]

    def get(self, request, snapshot_id: str, *args, **kwargs):
        snapshot = repository.get_snapshot(str(snapshot_id))
        if snapshot is None:
            return Response({"detail": "Class snapshot not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user_can_access_vessel(request.user, str(snapshot.get("vessel_id"))):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)

        blob_id = str(snapshot.get("pdf_blob_id") or "")
        blob = pdf_repository.get_blob(blob_id)
        if blob is None:
            return Response({"detail": "Class status PDF not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            absolute_path = resolve_pdf_blob_path(blob)
        except SuspiciousFileOperation:
            return Response({"detail": "Class status PDF path is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        if not absolute_path.is_file():
            return Response({"detail": "Class status PDF file is missing from storage."}, status=status.HTTP_404_NOT_FOUND)

        filename = get_valid_filename(str(blob.get("filename") or snapshot.get("filename") or absolute_path.name or "class-status.pdf")) or "class-status.pdf"
        response = FileResponse(absolute_path.open("rb"), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class ClassSnapshotReparseView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def post(self, request, snapshot_id: str, *args, **kwargs):
        if not has_request_certs_perm(request, RECONCILIATION_FORM_ID, RECONCILIATION_UPLOAD_PROCESS_ID):
            return Response({"detail": "You do not have access to re-parse class snapshots."}, status=status.HTTP_403_FORBIDDEN)
        if not is_reconciliation_uploader(request.user):
            return Response({"detail": "Only DPA or technical office users may re-parse class snapshots."}, status=status.HTTP_403_FORBIDDEN)
        before = repository.get_snapshot(str(snapshot_id))
        if before is None:
            return Response({"detail": "Class snapshot not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user_can_access_vessel(request.user, str(before.get("vessel_id"))):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            snapshot, run = run_class_snapshot_parser(str(snapshot_id), repository=repository)
            if snapshot is None:
                return Response({"detail": "Class snapshot not found."}, status=status.HTTP_404_NOT_FOUND)
            serialized_snapshot = serialize_class_snapshot(snapshot)
            serialized_run = serialize_reconciliation_run(run) if run else None
            record_audit_event(
                actor=request.user,
                action="reparse_snapshot",
                entity_type="class_status_snapshot",
                entity_id=serialized_snapshot["id"],
                vessel_id=serialized_snapshot["vesselId"],
                before=serialize_class_snapshot(before),
                after=serialized_snapshot,
                reason=str(request.data.get("reason") or "Class snapshot re-parse requested."),
                metadata={"source": "api.certs.class_snapshots.reparse"},
            )
        return Response({"snapshot": serialized_snapshot, "reconciliationRun": serialized_run})


def _validate_pdf_upload(uploaded_file) -> Response | None:
    if uploaded_file is None:
        return Response({"file": "Select a class status PDF to upload."}, status=status.HTTP_400_BAD_REQUEST)
    filename = str(getattr(uploaded_file, "name", "") or "")
    content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix != "pdf" or content_type not in {"application/pdf", "application/x-pdf", ""}:
        return Response({"file": "Class snapshot upload must be a PDF file."}, status=status.HTTP_400_BAD_REQUEST)
    size = int(getattr(uploaded_file, "size", 0) or 0)
    if size <= 0:
        return Response({"file": "Class snapshot PDF is empty."}, status=status.HTTP_400_BAD_REQUEST)
    if size > MAX_CLASS_SNAPSHOT_UPLOAD_BYTES:
        return Response({"file": "Class snapshot PDF must be 50 MB or smaller."}, status=status.HTTP_400_BAD_REQUEST)
    return None
