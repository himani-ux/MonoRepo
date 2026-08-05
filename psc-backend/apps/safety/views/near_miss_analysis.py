from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from django.utils import timezone
from django.utils.text import get_valid_filename
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from django.http import FileResponse

from apps.safety.models import EvidenceItem, Incident, IncidentEvidence, IncidentFact
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers import NearMissAnalysisFactSerializer, build_near_miss_analysis_payload
from apps.safety.serializers.near_miss_analysis import NearMissEvidenceSourceCreateSerializer
from apps.safety.views.near_miss import NearMissViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_NEAR_MISS_ANALYSIS_MUTATION_ROLES = {
    "MASTER",
    "CO",
    "CE",
    "HOD",
    "DPA",
    "FM",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "FLEET MANAGER",
    "HEAD OF DEPARTMENT",
}


class NearMissAnalysisViewMixin(NearMissViewMixin):
    lookup_url_kwarg = "id"
    process_permission_class = NearMissViewMixin.process_permission_class.requiring("SAF_P_002")

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method in {"POST", "PATCH", "PUT", "DELETE"}:
            permissions.append(self.process_permission_class())
        return permissions

    def get_near_miss(self) -> Incident:
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        near_miss = get_by_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Lightweight analysis is only available for near-miss records.")
        if near_miss.near_miss_priority != "HIGH":
            raise ValidationError("Lightweight analysis is only available for HIGH-priority near misses.")
        if near_miss.state == "SUPERSEDED" or near_miss.superseded_by_id:
            raise ValidationError(
                "Superseded near misses must continue in the incident workflow instead of the lightweight analysis workspace."
            )
        return near_miss

    def get_object(self):
        return self.get_near_miss()

    def _enforce_analysis_mutation_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_NEAR_MISS_ANALYSIS_MUTATION_ROLES:
            raise PermissionDenied("Only investigation roles may edit near-miss fact trees.")


class NearMissAnalysisWorkspaceView(NearMissAnalysisViewMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        near_miss = self.get_near_miss()
        return Response(
            build_near_miss_analysis_payload(
                near_miss,
                serializer_context=self.get_serializer_context(),
                fact_context={
                    "incident": near_miss,
                    "user_id": _resolve_actor_id(request.user),
                },
            ),
            status=status.HTTP_200_OK,
        )


class NearMissAnalysisEvidenceSourceCreateView(NearMissAnalysisViewMixin, generics.CreateAPIView):
    serializer_class = NearMissEvidenceSourceCreateSerializer
    queryset = EvidenceItem.objects.none()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    max_upload_bytes = 3 * 1024 * 1024
    allowed_content_types = {"image/jpeg", "image/jpg", "image/png"}
    allowed_suffixes = {".jpg", ".jpeg", ".png"}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_near_miss()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        self._enforce_analysis_mutation_role()
        near_miss = self.get_near_miss()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = request.FILES.get("photo") or request.FILES.get("file")
        evidence_type = serializer.validated_data["evidence_type"]
        if evidence_type == "PHOTO":
            if uploaded_file is None:
                raise ValidationError({"photo": "Attach a JPG or PNG image for photo evidence."})
            serializer.context["photo_metadata"] = self._store_photo(
                near_miss=near_miss,
                uploaded_file=uploaded_file,
            )
        elif uploaded_file is not None:
            raise ValidationError({"photo": "Image upload is only available for PHOTO evidence."})
        serializer.save()
        return Response(
            build_near_miss_analysis_payload(
                near_miss,
                serializer_context=self.get_serializer_context(),
                fact_context={
                    "incident": near_miss,
                    "user_id": _resolve_actor_id(request.user),
                },
            ),
            status=status.HTTP_201_CREATED,
        )

    def _store_photo(self, *, near_miss: Incident, uploaded_file) -> dict[str, object]:
        content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
        suffix = Path(str(uploaded_file.name or "")).suffix.lower()
        if content_type not in self.allowed_content_types or suffix not in self.allowed_suffixes:
            raise ValidationError({"photo": "Photo must be a JPG, JPEG, or PNG image."})

        size = int(getattr(uploaded_file, "size", 0) or 0)
        if size <= 0:
            raise ValidationError({"photo": "Photo file is empty."})
        if size > self.max_upload_bytes:
            raise ValidationError({"photo": "Photo must be 3MB or smaller."})

        relative_path, absolute_path = self._build_storage_path(
            vessel_id=str(near_miss.vessel_id),
            near_miss_id=str(near_miss.id),
            original_name=str(uploaded_file.name or "photo"),
        )
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        with absolute_path.open("wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        tab_row, _ = IncidentEvidence.objects.get_or_create(
            incident=near_miss,
            tab_code=IncidentEvidence.TabCode.POSITION,
            defaults={
                "summary": "Near miss photo evidence.",
                "entry_count": 0,
                "structured_data": {"source": "near_miss_analysis"},
                "status_chip": "Near miss photo evidence",
                "schema_version": near_miss.schema_version or 1,
                "created_by": _resolve_actor_id(self.request.user),
                "updated_by": _resolve_actor_id(self.request.user),
            },
        )
        metadata = {
            "attachment_path": relative_path,
            "byte_size": size,
            "content_type": content_type,
            "file_name": Path(relative_path).name,
            "original_name": str(uploaded_file.name or ""),
            "uploaded_at": timezone.now().isoformat(),
        }
        structured_data = dict(tab_row.structured_data or {})
        attachments = list(structured_data.get("attachments") or [])
        attachments.append(metadata)
        structured_data["attachments"] = attachments
        tab_row.structured_data = structured_data
        tab_row.entry_count = max(int(tab_row.entry_count or 0), len(attachments))
        tab_row.status_chip = f"{len(attachments)} near-miss photo attachment{'s' if len(attachments) != 1 else ''}"
        tab_row.updated_by = _resolve_actor_id(self.request.user)
        tab_row.updated_date = timezone.now()
        tab_row.save(update_fields=("structured_data", "entry_count", "status_chip", "updated_by", "updated_date"))
        return metadata

    def _build_storage_path(
        self,
        *,
        vessel_id: str,
        near_miss_id: int,
        original_name: str,
    ) -> tuple[str, Path]:
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        storage_root = Path(os.getenv("SAFETY_EXPORT_ROOT") or default_root).resolve(strict=False)
        suffix = Path(original_name).suffix.lower()
        safe_stem = Path(get_valid_filename(Path(original_name).stem or "photo")).stem[:80] or "photo"
        file_name = f"{safe_stem}-{uuid4().hex}{suffix}"
        safe_vessel_id = get_valid_filename(vessel_id or "unknown-vessel") or "unknown-vessel"
        relative_path = (
            Path("vessels")
            / safe_vessel_id
            / "near-miss"
            / str(near_miss_id)
            / "analysis"
            / "photos"
            / file_name
        )
        absolute_path = (storage_root / relative_path).resolve(strict=False)
        try:
            absolute_path.relative_to(storage_root)
        except ValueError as exc:
            raise ValidationError({"photo": "Invalid photo storage path."}) from exc
        return relative_path.as_posix(), absolute_path


class NearMissAnalysisEvidencePhotoView(NearMissAnalysisViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"

    def get(self, request, *args, **kwargs):
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        near_miss = get_by_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Photo attachments are only available for near-miss records.")
        evidence_item = get_by_id_or_pk(near_miss.evidence_items.all(), kwargs["evidence_id"])
        metadata = evidence_item.metadata_json or {}
        attachment_path = str(metadata.get("attachment_path") or "").strip()
        content_type = str(metadata.get("content_type") or "").strip()
        if not attachment_path or not content_type.startswith("image/"):
            raise ValidationError("Evidence item does not have a previewable photo attachment.")

        storage_root = Path(
            os.getenv("SAFETY_EXPORT_ROOT") or Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        ).resolve(strict=False)
        absolute_path = (storage_root / attachment_path).resolve(strict=False)
        try:
            absolute_path.relative_to(storage_root)
        except ValueError as exc:
            raise ValidationError("Invalid photo attachment path.") from exc
        if not absolute_path.is_file():
            raise ValidationError("Photo attachment file is missing from storage.")
        return FileResponse(absolute_path.open("rb"), content_type=content_type)


class NearMissAnalysisFactListCreateView(NearMissAnalysisViewMixin, generics.ListCreateAPIView):
    serializer_class = NearMissAnalysisFactSerializer
    queryset = IncidentFact.objects.none()

    def get_queryset(self):
        return self.get_near_miss().facts.order_by("sequence_index", "id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_near_miss()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        self._enforce_analysis_mutation_role()
        return super().create(request, *args, **kwargs)


class NearMissAnalysisFactDetailView(NearMissAnalysisViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NearMissAnalysisFactSerializer
    lookup_url_kwarg = "fact_id"

    def get_queryset(self):
        return self.get_near_miss().facts.order_by("sequence_index", "id")

    def get_object(self):
        return get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_near_miss()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def update(self, request, *args, **kwargs):
        self._enforce_analysis_mutation_role()
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._enforce_analysis_mutation_role()
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
