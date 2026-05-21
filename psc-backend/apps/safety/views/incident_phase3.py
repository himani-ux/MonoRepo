from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from django.utils.text import get_valid_filename
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.safety.models import EvidenceDeadlineTask, EvidenceItem, Incident, IncidentEvidence
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.serializers.incident_phase3 import (
    ChainOfCustodyCreateSerializer,
    ChainOfCustodySerializer,
    ChainOfCustodyTransferSerializer,
    EvidenceDeadlineTaskSerializer,
    EvidenceDeadlineTaskUpdateSerializer,
    EvidenceItemMatrixSerializer,
    IncidentPhase3WorkspaceWriteSerializer,
    TAB_KEY_TO_CODE,
    WitnessInterviewSerializer,
    build_phase3_workspace_payload,
)
from apps.safety.services import capture_model_state, record_field_changes
from apps.safety.views.incident import IncidentViewMixin, _normalized_role, _resolve_actor_id


ALLOWED_PHASE_3_MUTATION_ROLES = {
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


class IncidentPhase3ViewMixin(IncidentViewMixin):
    process_permission_class = IncidentViewMixin.process_permission_class.requiring("SAF_P_002")

    def get_incident(self) -> Incident:
        queryset = self._apply_filters(Incident.objects.filter(is_deleted=False))
        incident = get_by_public_id_or_pk(queryset, self.kwargs[self.lookup_url_kwarg])
        if incident.current_phase != 3:
            raise ValidationError("Phase 3 evidence can only be edited while current_phase = 3.")
        return incident

    def get_object(self):
        return self.get_incident()

    def _enforce_phase_3_mutation_role(self) -> None:
        if _normalized_role(self.request.user) not in ALLOWED_PHASE_3_MUTATION_ROLES:
            raise PermissionDenied("Only investigation roles may edit Phase 3 evidence.")


class IncidentPhase3EvidenceView(IncidentPhase3ViewMixin, generics.RetrieveUpdateAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False).prefetch_related(
        "evidence_tabs",
        "chain_of_custody_rows",
        "evidence_items",
        "evidence_deadline_tasks",
        "witness_interviews",
    )
    serializer_class = IncidentPhase3WorkspaceWriteSerializer

    def retrieve(self, request, *args, **kwargs):
        incident = self.get_object()
        return Response(build_phase3_workspace_payload(incident), status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        incident = self.get_object()
        self._enforce_phase_3_mutation_role()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor_id = _resolve_actor_id(request.user)
        old_state = capture_model_state(
            incident,
            field_names=("marine_docs_checklist_done", "cargo_evidence_applicable", "health_fatigue_applicable"),
        )
        for key, tab_payload in serializer.validated_data.items():
            self._upsert_tab(incident, key, tab_payload, actor_id=actor_id)

        self._sync_incident_sentinels(incident, serializer.validated_data, actor_id=actor_id)
        record_field_changes(
            incident,
            old_state,
            user=request.user,
            field_names=tuple(old_state.keys()),
            change_reason="Phase 3 evidence update",
        )
        incident.refresh_from_db()
        incident = Incident.objects.prefetch_related(
            "evidence_tabs",
            "chain_of_custody_rows",
            "evidence_items",
            "evidence_deadline_tasks",
            "witness_interviews",
        ).get(pk=incident.pk)
        return Response(build_phase3_workspace_payload(incident), status=status.HTTP_200_OK)

    def _upsert_tab(self, incident: Incident, key: str, payload: dict[str, object], *, actor_id: str) -> None:
        tab_code = {
            "position": IncidentEvidence.TabCode.POSITION,
            "people": IncidentEvidence.TabCode.PEOPLE,
            "parts": IncidentEvidence.TabCode.PARTS,
            "paper": IncidentEvidence.TabCode.PAPER,
            "electronic": IncidentEvidence.TabCode.ELECTRONIC,
        }[key]
        row, _ = IncidentEvidence.objects.get_or_create(
            incident=incident,
            tab_code=tab_code,
            defaults={
                "created_by": actor_id,
                "updated_by": actor_id,
                "schema_version": incident.schema_version or 1,
            },
        )
        for field_name, value in payload.items():
            setattr(row, field_name, value)
        row.updated_by = actor_id
        row.updated_date = timezone.now()
        row.save()

    def _sync_incident_sentinels(self, incident: Incident, tab_payloads: dict[str, dict[str, object]], *, actor_id: str) -> None:
        update_fields: list[str] = []
        paper_payload = tab_payloads.get("paper")
        if paper_payload is not None:
            structured_data = paper_payload.get("structured_data") or {}
            incident.marine_docs_checklist_done = bool(structured_data.get("checklist_complete"))
            incident.cargo_evidence_applicable = bool(structured_data.get("cargo_overlay_items") or [])
            update_fields.extend(["marine_docs_checklist_done", "cargo_evidence_applicable"])

        people_payload = tab_payloads.get("people")
        if people_payload is not None:
            structured_data = people_payload.get("structured_data") or {}
            incident.health_fatigue_applicable = bool(structured_data.get("health_fatigue"))
            update_fields.append("health_fatigue_applicable")

        if update_fields:
            incident.updated_by = actor_id
            incident.updated_date = timezone.now()
            incident.save(update_fields=[*update_fields, "updated_by", "updated_date"])


def sync_evidence_tab_count(
    *,
    incident: Incident,
    tab_code: str,
    minimum_count: int,
    actor_id: str,
    summary: str = "",
    status_chip: str = "",
) -> IncidentEvidence:
    row, _ = IncidentEvidence.objects.get_or_create(
        incident=incident,
        tab_code=tab_code,
        defaults={
            "created_by": actor_id,
            "updated_by": actor_id,
            "schema_version": incident.schema_version or 1,
        },
    )
    update_fields = ["entry_count", "updated_by", "updated_date"]
    row.entry_count = max(int(row.entry_count or 0), minimum_count)
    if summary and not (row.summary or "").strip():
        row.summary = summary
        update_fields.append("summary")
    if status_chip:
        row.status_chip = status_chip
        update_fields.append("status_chip")
    row.updated_by = actor_id
    row.updated_date = timezone.now()
    row.save(update_fields=update_fields)
    return row


class IncidentPhase3AttachmentUploadView(IncidentPhase3ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    parser_classes = (MultiPartParser, FormParser)
    max_upload_bytes = 3 * 1024 * 1024
    allowed_content_types = {"image/jpeg", "image/jpg", "image/png"}
    allowed_suffixes = {".jpg", ".jpeg", ".png"}

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        self._enforce_phase_3_mutation_role()
        actor_id = _resolve_actor_id(request.user)
        tab_key = str(request.data.get("tab_key") or "").strip().lower()
        if tab_key not in TAB_KEY_TO_CODE:
            raise ValidationError({"tab_key": "Select a valid Phase 3 evidence tab."})

        uploaded_file = request.FILES.get("photo") or request.FILES.get("file")
        if uploaded_file is None:
            raise ValidationError({"photo": "Select a photo to upload."})

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
            vessel_id=str(incident.vessel_id),
            incident_id=int(incident.id),
            tab_key=tab_key,
            original_name=str(uploaded_file.name or "photo"),
        )
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        with absolute_path.open("wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        tab_code = TAB_KEY_TO_CODE[tab_key]
        tab_row, _ = IncidentEvidence.objects.get_or_create(
            incident=incident,
            tab_code=tab_code,
            defaults={
                "created_by": actor_id,
                "updated_by": actor_id,
                "schema_version": incident.schema_version or 1,
            },
        )
        metadata = {
            "attachment_path": relative_path,
            "byte_size": size,
            "content_type": content_type,
            "file_name": Path(relative_path).name,
            "original_name": str(uploaded_file.name or ""),
            "tab_key": tab_key,
            "uploaded_at": timezone.now().isoformat(),
        }
        structured_data = dict(tab_row.structured_data or {})
        attachments = list(structured_data.get("attachments") or [])
        attachments.append(metadata)
        structured_data["attachments"] = attachments
        tab_row.structured_data = structured_data
        tab_row.entry_count = max(int(tab_row.entry_count or 0), len(attachments))
        tab_row.status_chip = f"{len(attachments)} attachment{'s' if len(attachments) != 1 else ''}"
        tab_row.updated_by = actor_id
        tab_row.updated_date = timezone.now()
        tab_row.save(update_fields=["structured_data", "entry_count", "status_chip", "updated_by", "updated_date"])

        EvidenceItem.objects.create(
            incident=incident,
            evidence_tab=tab_row,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title=metadata["file_name"],
            description=str(request.data.get("description") or ""),
            source_label=str(tab_code),
            metadata_json=metadata,
            created_by=actor_id,
            updated_by=actor_id,
            schema_version=incident.schema_version or 1,
        )

        incident = Incident.objects.prefetch_related(
            "evidence_tabs",
            "chain_of_custody_rows",
            "evidence_items",
            "evidence_deadline_tasks",
            "witness_interviews",
        ).get(pk=incident.pk)
        return Response(
            {
                "attachment": metadata,
                "workspace": build_phase3_workspace_payload(incident),
            },
            status=status.HTTP_201_CREATED,
        )

    def _build_storage_path(
        self,
        *,
        vessel_id: str,
        incident_id: int,
        tab_key: str,
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
            / "incidents"
            / str(incident_id)
            / "phase-3"
            / tab_key
            / file_name
        )
        absolute_path = (storage_root / relative_path).resolve(strict=False)
        try:
            absolute_path.relative_to(storage_root)
        except ValueError as exc:
            raise ValidationError({"photo": "Invalid photo storage path."}) from exc
        return relative_path.as_posix(), absolute_path


class IncidentPhase3ChainOfCustodyView(IncidentPhase3ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)

    def get(self, request, *args, **kwargs):
        incident = self.get_object()
        rows = incident.chain_of_custody_rows.order_by("collection_timestamp", "id")
        return Response(ChainOfCustodySerializer(rows, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        incident = self.get_object()
        self._enforce_phase_3_mutation_role()
        actor_id = _resolve_actor_id(request.user)

        if "chain_of_custody_id" in request.data:
            serializer = ChainOfCustodyTransferSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            row = incident.chain_of_custody_rows.get(pk=serializer.validated_data["chain_of_custody_id"])
            old_state = capture_model_state(row, field_names=("handover_log", "current_holder"))
            handover_log = list(row.handover_log)
            handover_log.append(
                {
                    "handover_timestamp": serializer.validated_data["handover_timestamp"].isoformat(),
                    "handover_from": serializer.validated_data["handover_from"],
                    "handover_to": serializer.validated_data["handover_to"],
                }
            )
            row.handover_log = handover_log
            row.current_holder = serializer.validated_data["handover_to"]
            row.updated_by = actor_id
            row.updated_date = timezone.now()
            row.save(update_fields=["handover_log", "current_holder", "updated_by", "updated_date"])
            record_field_changes(
                row,
                old_state,
                user=request.user,
                field_names=("handover_log", "current_holder"),
                change_reason="Chain-of-custody transfer",
                parent_table="vims_safety_chain_of_custody",
            )
            return Response(ChainOfCustodySerializer(row).data, status=status.HTTP_200_OK)

        serializer = ChainOfCustodyCreateSerializer(
            data=request.data,
            context={"incident": incident, "user_id": actor_id},
        )
        serializer.is_valid(raise_exception=True)
        row = serializer.save()
        if not incident.chain_of_custody_ok:
            incident.chain_of_custody_ok = True
            incident.updated_by = actor_id
            incident.updated_date = timezone.now()
            incident.save(update_fields=["chain_of_custody_ok", "updated_by", "updated_date"])
        return Response(ChainOfCustodySerializer(row).data, status=status.HTTP_201_CREATED)


class IncidentPhase3EvidenceMatrixView(IncidentPhase3ViewMixin, generics.ListCreateAPIView):
    lookup_url_kwarg = "id"
    queryset = EvidenceItem.objects.none()
    serializer_class = EvidenceItemMatrixSerializer

    def get_queryset(self):
        incident = self.get_incident()
        return incident.evidence_items.filter(item_type=EvidenceItem.ItemType.MATRIX).order_by("id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        self._enforce_phase_3_mutation_role()
        return super().create(request, *args, **kwargs)


class IncidentPhase3InterviewView(IncidentPhase3ViewMixin, generics.ListCreateAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.none()
    serializer_class = WitnessInterviewSerializer

    def get_queryset(self):
        incident = self.get_incident()
        return incident.witness_interviews.order_by("id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["incident"] = self.get_incident()
        context["user_id"] = _resolve_actor_id(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        self._enforce_phase_3_mutation_role()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        row = serializer.save()
        incident = self.get_incident()
        actor_id = _resolve_actor_id(self.request.user)
        sync_evidence_tab_count(
            incident=incident,
            tab_code=IncidentEvidence.TabCode.PEOPLE,
            minimum_count=incident.witness_interviews.count(),
            actor_id=actor_id,
            summary="Witness/interview evidence captured.",
            status_chip=f"{incident.witness_interviews.count()} interview(s)",
        )
        return row


class IncidentPhase3DeadlineTaskView(IncidentPhase3ViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    serializer_class = EvidenceDeadlineTaskUpdateSerializer

    def patch(self, request, *args, **kwargs):
        incident = self.get_object()
        self._enforce_phase_3_mutation_role()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = get_by_public_id_or_pk(incident.evidence_deadline_tasks.all(), self.kwargs["task_id"])
        next_status = serializer.validated_data["status"]
        task.status = next_status
        task.justification = serializer.validated_data.get("justification")
        if next_status == EvidenceDeadlineTask.Status.COMPLETED and task.completed_at is None:
            task.completed_at = timezone.now()
        elif next_status == EvidenceDeadlineTask.Status.PENDING:
            task.completed_at = None
        task.updated_by = _resolve_actor_id(request.user)
        task.updated_date = timezone.now()
        task.save(update_fields=["status", "justification", "completed_at", "updated_by", "updated_date"])
        return Response(EvidenceDeadlineTaskSerializer(task).data, status=status.HTTP_200_OK)
