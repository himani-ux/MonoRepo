from __future__ import annotations

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    ONBOARDING_CREATE_PROCESS_ID,
    ONBOARDING_FORM_ID,
    ONBOARDING_ROLLBACK_PROCESS_ID,
    ONBOARDING_SIGNOFF_PROCESS_ID,
    HasOnboardingReadPermission,
    has_request_certs_perm,
    user_can_access_vessel,
)
from apps.certs.serializers.onboarding import (
    OnboardingBatchCommitSerializer,
    CoverageOverrideSerializer,
    OnboardingActionReasonSerializer,
    OnboardingBatchCreateSerializer,
    OnboardingProfileSerializer,
    OnboardingRollbackSerializer,
    OnboardingStartSerializer,
    serialize_batch,
    serialize_gap_fill_state,
    serialize_onboarding_hub_row,
    serialize_validation_result,
    serialize_vessel_config,
    serialize_wizard_state,
)
from apps.certs.services.audit_log import record_audit_event
from apps.certs.services.onboarding_repository import OnboardingRepository


repository = OnboardingRepository()


class OnboardingWriteMixin:
    required_process_id = ONBOARDING_CREATE_PROCESS_ID

    def _has_write_permission(self, request) -> bool:
        return has_request_certs_perm(request, ONBOARDING_FORM_ID, self.required_process_id)


class OnboardingSessionListCreateView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "results": [
                    serialize_onboarding_hub_row(row)
                    for row in repository.list_onboarding_sessions()
                ]
            }
        )

    def post(self, request, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to start Certs onboarding."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OnboardingStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vessel_identifier = serializer.validated_data.get("vesselId") or serializer.validated_data.get("imo")
        config = repository.start_onboarding(
            vessel_identifier=str(vessel_identifier),
            ship_type=serializer.validated_data.get("shipType") or None,
            actor=request.user,
        )
        if config is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        state = repository.get_wizard_state(str(config["vessel_id"]))
        if state is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        record_audit_event(
            actor=request.user,
            action="onboarding_step_complete",
            entity_type="vessel_config",
            entity_id=str(config["vessel_id"]),
            vessel_id=str(config["vessel_id"]),
            before=None,
            after=serialize_vessel_config(config),
            reason="Onboarding session started.",
            metadata={"source": "api.certs.onboarding", "step": 1},
        )
        return Response(serialize_wizard_state(state), status=status.HTTP_201_CREATED)


class OnboardingSessionDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]

    def get(self, request, vessel_id: str, *args, **kwargs):
        state = repository.get_wizard_state(str(vessel_id))
        if state is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_vessel_id = str((state.get("vessel") or {}).get("vessel_id") or "")
        if not user_can_access_vessel(request.user, resolved_vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        return Response(serialize_wizard_state(state))


class OnboardingProfileView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]

    def post(self, request, vessel_id: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to update onboarding profile."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OnboardingProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vessel = repository.resolve_vessel(str(vessel_id))
        if vessel is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_vessel_id = str(vessel["vessel_id"])
        if not user_can_access_vessel(request.user, resolved_vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            before, after = repository.save_profile(
                vessel_id=resolved_vessel_id,
                values=serializer.validated_data,
                actor=request.user,
            )
            record_audit_event(
                actor=request.user,
                action="onboarding_step_complete",
                entity_type="vessel_config",
                entity_id=resolved_vessel_id,
                vessel_id=resolved_vessel_id,
                before=serialize_vessel_config(before),
                after=serialize_vessel_config(after),
                reason="Onboarding vessel profile saved.",
                metadata={"source": "api.certs.onboarding.profile", "step": 2},
            )
        return Response({"vessel": vessel, "config": serialize_vessel_config(after)})


class OnboardingBatchCreateView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]

    def post(self, request, vessel_id: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to create onboarding batches."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OnboardingBatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vessel = repository.resolve_vessel(str(vessel_id))
        if vessel is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_vessel_id = str(vessel["vessel_id"])
        if not user_can_access_vessel(request.user, resolved_vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        pdf_blob_ids = [str(blob_id) for blob_id in serializer.validated_data["pdfBlobIds"]]
        with transaction.atomic():
            batch = repository.create_batch(
                vessel_id=resolved_vessel_id,
                pdf_blob_ids=pdf_blob_ids,
                onboarding_session_id=(
                    str(serializer.validated_data["onboardingSessionId"])
                    if serializer.validated_data.get("onboardingSessionId")
                    else None
                ),
                actor=request.user,
            )
            serialized = serialize_batch(batch)
            record_audit_event(
                actor=request.user,
                action="onboarding_step_complete",
                entity_type="batch_ingest",
                entity_id=serialized["id"],
                vessel_id=resolved_vessel_id,
                before=None,
                after=serialized,
                reason="Onboarding PDF batch ready for gap-fill review.",
                metadata={"source": "api.certs.onboarding.batch", "step": 3},
            )
        return Response(serialized, status=status.HTTP_201_CREATED)


class OnboardingBatchDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]

    def get(self, request, batch_id: str, *args, **kwargs):
        state = repository.get_batch_gap_fill(str(batch_id))
        if state is None:
            return Response({"detail": "Onboarding batch not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str((state.get("batch") or {}).get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        return Response(serialize_gap_fill_state(state))


class OnboardingBatchPreviewView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]

    def post(self, request, batch_id: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to preview onboarding validation."}, status=status.HTTP_403_FORBIDDEN)
        state = repository.get_batch_gap_fill(str(batch_id))
        if state is None:
            return Response({"detail": "Onboarding batch not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str((state.get("batch") or {}).get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            result = repository.evaluate_batch_validation(str(batch_id))
            if result is None:
                return Response({"detail": "Onboarding batch not found."}, status=status.HTTP_404_NOT_FOUND)
            serialized = serialize_validation_result(result)
            if not serialized["validationBlocks"]:
                idempotency = repository.evaluate_batch_idempotency(str(batch_id), supersede_decisions=[])
                if idempotency is None:
                    return Response({"detail": "Onboarding batch not found."}, status=status.HTTP_404_NOT_FOUND)
                if idempotency.get("blocks"):
                    combined_blocks = [*serialized["validationBlocks"], *idempotency["blocks"]]
                    batch = repository.persist_batch_validation(
                        str(batch_id),
                        blocks=combined_blocks,
                        warns=serialized["validationWarns"],
                    )
                    serialized = {
                        **serialized,
                        "batch": serialize_batch(batch),
                        "validationBlocks": combined_blocks,
                        "canCommit": False,
                    }
            if serialized["validationBlocks"]:
                record_audit_event(
                    actor=request.user,
                    action="validation_block",
                    entity_type="batch_ingest",
                    entity_id=str(batch_id),
                    vessel_id=vessel_id,
                    before=None,
                    after=serialized,
                    reason="Onboarding batch validation blocked commit.",
                    metadata={
                        "source": "api.certs.onboarding.batch.preview",
                        "step": 3,
                        "blockCodes": [entry.get("code") for entry in serialized["validationBlocks"]],
                    },
                )
        return Response(serialized)


class OnboardingBatchCommitView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]
    required_process_id = ONBOARDING_SIGNOFF_PROCESS_ID

    def post(self, request, batch_id: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to commit onboarding batches."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OnboardingBatchCommitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        state = repository.get_batch_gap_fill(str(batch_id))
        if state is None:
            return Response({"detail": "Onboarding batch not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str((state.get("batch") or {}).get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            result = repository.evaluate_batch_validation(str(batch_id))
            if result is None:
                return Response({"detail": "Onboarding batch not found."}, status=status.HTTP_404_NOT_FOUND)
            serialized = serialize_validation_result(result)
            if serialized["validationBlocks"]:
                record_audit_event(
                    actor=request.user,
                    action="validation_block",
                    entity_type="batch_ingest",
                    entity_id=str(batch_id),
                    vessel_id=vessel_id,
                    before=None,
                    after=serialized,
                    reason="Onboarding batch commit blocked by D-CERT-116 validation.",
                    metadata={
                        "source": "api.certs.onboarding.batch.commit",
                        "step": 3,
                        "blockCodes": [entry.get("code") for entry in serialized["validationBlocks"]],
                    },
                )
                return Response({"detail": "Validation blocks must be resolved before commit.", **serialized}, status=status.HTTP_409_CONFLICT)
            if serialized["validationWarns"] and not serializer.validated_data["acknowledgeWarnings"]:
                return Response({"detail": "D-CERT-116 warnings require DPA acknowledgment.", **serialized}, status=status.HTTP_409_CONFLICT)
            idempotency = repository.evaluate_batch_idempotency(
                str(batch_id),
                supersede_decisions=serializer.validated_data.get("supersedeDecisions") or [],
            )
            if idempotency is None:
                return Response({"detail": "Onboarding batch not found."}, status=status.HTTP_404_NOT_FOUND)
            if idempotency.get("blocks"):
                combined_blocks = [*serialized["validationBlocks"], *idempotency["blocks"]]
                batch = repository.persist_batch_validation(
                    str(batch_id),
                    blocks=combined_blocks,
                    warns=serialized["validationWarns"],
                )
                supersede_blocked = {
                    **serialized,
                    "batch": serialize_batch(batch),
                    "validationBlocks": combined_blocks,
                    "canCommit": False,
                }
                return Response(
                    {"detail": "Supersede confirmation is required before commit.", **supersede_blocked},
                    status=status.HTTP_409_CONFLICT,
                )
            applied_idempotency = repository.apply_batch_idempotency(idempotency, actor=request.user)
            for skipped in applied_idempotency.get("skippedDuplicates") or []:
                record_audit_event(
                    actor=request.user,
                    action="upload_pdf",
                    entity_type="pdf_blob",
                    entity_id=str(skipped.get("blobId") or ""),
                    vessel_id=vessel_id,
                    before=None,
                    after=skipped,
                    reason="Duplicate PDF silently skipped per D-CERT-118.",
                    metadata={
                        "source": "api.certs.onboarding.batch.commit",
                        "step": 3,
                        "skippedDuplicate": True,
                        "existingBlobId": skipped.get("existingBlobId"),
                        "certificateNumber": skipped.get("certificateNumber"),
                        "sha256": skipped.get("sha256"),
                    },
                )
            for superseded in applied_idempotency.get("supersededPdfs") or []:
                record_audit_event(
                    actor=request.user,
                    action="supersede_pdf",
                    entity_type="pdf_blob",
                    entity_id=str(superseded.get("blobId") or ""),
                    vessel_id=vessel_id,
                    before={"blobId": superseded.get("existingBlobId"), "sha256": superseded.get("oldSha256")},
                    after={"blobId": superseded.get("blobId"), "sha256": superseded.get("newSha256")},
                    reason="PDF supersession confirmed per D-CERT-118.",
                    metadata={
                        "source": "api.certs.onboarding.batch.commit",
                        "step": 3,
                        "existingBlobId": superseded.get("existingBlobId"),
                        "trackedItemId": superseded.get("trackedItemId"),
                        "certificateNumber": superseded.get("certificateNumber"),
                    },
                )
            repository.create_batch_report_csv(str(batch_id), actor=request.user)
            committed_batch = repository.mark_batch_committed(str(batch_id), actor=request.user)
            committed = {
                **serialized,
                "batch": serialize_batch(committed_batch),
            }
            record_audit_event(
                actor=request.user,
                action="onboarding_step_complete",
                entity_type="batch_ingest",
                entity_id=str(batch_id),
                vessel_id=vessel_id,
                before=serialized.get("batch"),
                after=committed["batch"],
                reason="Onboarding batch committed after D-CERT-116 validation.",
                metadata={
                    "source": "api.certs.onboarding.batch.commit",
                    "step": 3,
                    "warningAck": bool(serializer.validated_data["acknowledgeWarnings"]),
                    "warningCodes": [entry.get("code") for entry in serialized["validationWarns"]],
                    "reportCsvBlobId": committed["batch"].get("reportCsvBlobId"),
                },
            )
        return Response(committed)


class OnboardingCoverageOverrideView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]

    def post(self, request, vessel_id: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to override coverage."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CoverageOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vessel = repository.resolve_vessel(str(vessel_id))
        if vessel is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_vessel_id = str(vessel["vessel_id"])
        if not user_can_access_vessel(request.user, resolved_vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            before, after = repository.update_coverage_override(
                vessel_id=resolved_vessel_id,
                reason=serializer.validated_data["reason"],
                actor=request.user,
            )
            record_audit_event(
                actor=request.user,
                action="coverage_override",
                entity_type="vessel_config",
                entity_id=resolved_vessel_id,
                vessel_id=resolved_vessel_id,
                before=serialize_vessel_config(before),
                after=serialize_vessel_config(after),
                reason=serializer.validated_data["reason"],
                metadata={"source": "api.certs.onboarding.coverage_override", "step": 6},
            )
        return Response({"config": serialize_vessel_config(after)})


class OnboardingFmSignoffView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]
    required_process_id = ONBOARDING_SIGNOFF_PROCESS_ID

    def post(self, request, vessel_id: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to sign off Certs onboarding."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OnboardingActionReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vessel = repository.resolve_vessel(str(vessel_id))
        if vessel is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_vessel_id = str(vessel["vessel_id"])
        with transaction.atomic():
            before, after = repository.mark_active(vessel_id=resolved_vessel_id, actor=request.user)
            record_audit_event(
                actor=request.user,
                action="fm_signoff",
                entity_type="vessel_config",
                entity_id=resolved_vessel_id,
                vessel_id=resolved_vessel_id,
                before=serialize_vessel_config(before),
                after=serialize_vessel_config(after),
                reason=serializer.validated_data.get("reason") or "FM signed off onboarding.",
                metadata={
                    "source": "api.certs.onboarding.fm_signoff",
                    "step": 7,
                    "welcome_notification_deferred_to_phase_6": True,
                },
            )
        return Response({"config": serialize_vessel_config(after)})


class OnboardingRollbackView(OnboardingWriteMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasOnboardingReadPermission]
    required_process_id = ONBOARDING_ROLLBACK_PROCESS_ID

    def post(self, request, vessel_id: str, *args, **kwargs):
        if not self._has_write_permission(request):
            return Response({"detail": "You do not have access to rollback Certs onboarding."}, status=status.HTTP_403_FORBIDDEN)
        if not _is_dpa_onboarding_user(request.user):
            return Response({"detail": "Only DPA may rollback Certs onboarding."}, status=status.HTTP_403_FORBIDDEN)
        serializer = OnboardingRollbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]
        vessel = repository.resolve_vessel(str(vessel_id))
        if vessel is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_vessel_id = str(vessel["vessel_id"])
        if not user_can_access_vessel(request.user, resolved_vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        current_config = repository.get_vessel_config(resolved_vessel_id)
        if current_config is None:
            return Response({"detail": "Onboarding session not found."}, status=status.HTTP_404_NOT_FOUND)
        if current_config.get("lifecycle_status") != "onboarding_in_progress":
            return Response(
                {"detail": "Onboarding rollback is available only before FM sign-off."},
                status=status.HTTP_409_CONFLICT,
            )
        with transaction.atomic():
            before, after, summary = repository.rollback_onboarding(vessel_id=resolved_vessel_id, actor=request.user)
            record_audit_event(
                actor=request.user,
                action="onboarding_rollback",
                entity_type="vessel_config",
                entity_id=resolved_vessel_id,
                vessel_id=resolved_vessel_id,
                before=serialize_vessel_config(before),
                after=serialize_vessel_config(after),
                reason=reason,
                metadata={"source": "api.certs.onboarding.rollback", **summary},
            )
        return Response({"config": serialize_vessel_config(after)})


def _is_dpa_onboarding_user(user) -> bool:
    role_text = " ".join(
        str(getattr(user, attr_name, "") or "").strip().upper()
        for attr_name in ("role", "role_name", "safety_role_name")
    )
    return any(marker in role_text for marker in ("DPA", "SEQ MANAGER", "SUPER ADMIN", "SYSTEM ADMIN"))
