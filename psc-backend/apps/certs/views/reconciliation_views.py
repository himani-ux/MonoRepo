from __future__ import annotations

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    RECONCILIATION_FORM_ID,
    RECONCILIATION_MAPPING_PROCESS_ID,
    RECONCILIATION_REVIEW_PROCESS_ID,
    HasReconciliationReadPermission,
    has_request_certs_perm,
    is_master_user,
    is_reconciliation_mapping_writer,
    is_reconciliation_reviewer,
    user_can_access_vessel,
)
from apps.certs.serializers.snapshot import (
    ClassCodeMappingAddSerializer,
    serialize_class_code_mapping,
    serialize_master_reconciliation_message,
    serialize_reconciliation_flag,
    serialize_reconciliation_run,
)
from apps.certs.services.audit_log import record_audit_event, resolve_actor_id
from apps.certs.services.reconciliation import ReconciliationRepository


repository = ReconciliationRepository()


class ReconciliationRunListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def get(self, request, *args, **kwargs):
        page = repository.list_runs(
            vessel_id=request.query_params.get("vesselId") or None,
            class_society=request.query_params.get("classSociety") or None,
            parse_status=request.query_params.get("parseStatus") or None,
            page=int(request.query_params.get("page") or 1),
            page_size=int(request.query_params.get("pageSize") or 25),
        )
        return Response({"count": page["count"], "results": [serialize_reconciliation_run(row) for row in page["results"]]})


class ReconciliationRunDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def get(self, request, run_id: str, *args, **kwargs):
        detail = repository.get_run_detail(str(run_id))
        if detail is None:
            return Response({"detail": "Reconciliation run not found."}, status=status.HTTP_404_NOT_FOUND)
        run = detail["run"]
        if not user_can_access_vessel(request.user, str(run.get("vessel_id"))):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        data = serialize_reconciliation_run(run)
        data["flags"] = [serialize_reconciliation_flag(flag) for flag in detail["flags"]]
        return Response(data)


class ReconciliationMasterMessageListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def get(self, request, *args, **kwargs):
        if str(getattr(request.user, "user_type", "") or "").upper() != "VESSEL":
            return Response({"detail": "Only vessel users may view office class-status messages."}, status=status.HTTP_403_FORBIDDEN)
        vessel_id = _message_vessel_id(request)
        if not vessel_id:
            return Response({"detail": "No vessel is linked to this login."}, status=status.HTTP_400_BAD_REQUEST)
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        include_reviewed = str(request.query_params.get("includeReviewed") or "").strip().lower() in {"1", "true", "yes"}
        page = repository.list_master_messages(
            vessel_id=vessel_id,
            include_reviewed=include_reviewed,
            page=_positive_int(request.query_params.get("page"), 1),
            page_size=_positive_int(request.query_params.get("pageSize", request.query_params.get("page_size")), 50),
        )
        return Response(
            {
                "count": page["count"],
                "results": [serialize_master_reconciliation_message(row) for row in page["results"]],
            }
        )


class ReconciliationMasterMessageAcknowledgeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def post(self, request, flag_id: str, *args, **kwargs):
        if str(getattr(request.user, "user_type", "") or "").upper() != "VESSEL":
            return Response({"detail": "Only vessel users may review office class-status messages."}, status=status.HTTP_403_FORBIDDEN)
        if not is_master_user(request.user):
            return Response({"detail": "Only the Master may mark this office message reviewed."}, status=status.HTTP_403_FORBIDDEN)
        message = repository.get_master_message(str(flag_id))
        if message is None:
            return Response({"detail": "Office message not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str(message.get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        if message.get("master_reviewed_at"):
            return Response(serialize_master_reconciliation_message(message))
        note = str(request.data.get("note") or request.data.get("reason") or "").strip()
        if len(note) > 2000:
            return Response({"note": "Note must be 2000 characters or fewer."}, status=status.HTTP_400_BAD_REQUEST)

        before = serialize_master_reconciliation_message(message)
        record_audit_event(
            actor=request.user,
            action="reconciliation_review",
            entity_type="reconciliation_flag",
            entity_id=str(flag_id),
            vessel_id=vessel_id,
            before=before,
            after={**before, "masterReviewed": True},
            reason=note or "Reviewed by vessel Master.",
            metadata={
                "source": "api.certs.reconciliation.master_messages.acknowledge",
                "resolution_action": "master_reviewed",
                "run_id": before["runId"],
            },
        )
        refreshed = repository.get_master_message(str(flag_id)) or message
        return Response(serialize_master_reconciliation_message(refreshed))


class ReconciliationFlagMarkReviewedView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def post(self, request, flag_id: str, *args, **kwargs):
        return _review_flag(request, str(flag_id), action="marked_reviewed")


class ReconciliationFlagNotifyMasterView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def post(self, request, flag_id: str, *args, **kwargs):
        return _review_flag(request, str(flag_id), action="notified_master")


class ReconciliationFlagAddMappingView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasReconciliationReadPermission]

    def post(self, request, flag_id: str, *args, **kwargs):
        if not has_request_certs_perm(request, RECONCILIATION_FORM_ID, RECONCILIATION_MAPPING_PROCESS_ID):
            return Response({"detail": "You do not have access to edit ClassCodeMapping."}, status=status.HTTP_403_FORBIDDEN)
        if not is_reconciliation_mapping_writer(request.user):
            return Response({"detail": "Only DPA may edit ClassCodeMapping."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClassCodeMappingAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        context = repository.get_flag_context(str(flag_id))
        if context is None:
            return Response({"detail": "Reconciliation flag not found."}, status=status.HTTP_404_NOT_FOUND)
        if not user_can_access_vessel(request.user, str(context.get("vessel_id"))):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            try:
                result = repository.add_mapping_for_flag(
                    str(flag_id),
                    catalog_id=str(serializer.validated_data["catalogId"]),
                    cert_or_survey_kind=str(serializer.validated_data["certOrSurveyKind"]),
                    notes=serializer.validated_data.get("notes") or None,
                    actor_id=resolve_actor_id(request.user),
                )
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            if result is None or result.get("after") is None:
                return Response({"detail": "Reconciliation flag not found."}, status=status.HTTP_404_NOT_FOUND)

            before_mapping = serialize_class_code_mapping(result.get("before"))
            after_mapping = serialize_class_code_mapping(result.get("after"))
            after_flag = serialize_reconciliation_flag(result["flag_after"]) if result.get("flag_after") else None
            new_run = serialize_reconciliation_run(result["run"]) if result.get("run") else None
            record_audit_event(
                actor=request.user,
                action=str(result["audit_action"]),
                entity_type="class_code_mapping",
                entity_id=after_mapping["id"] if after_mapping else None,
                vessel_id=str(context.get("vessel_id")),
                before=before_mapping,
                after=after_mapping,
                reason=str(serializer.validated_data["reason"]),
                metadata={
                    "source": "api.certs.reconciliation.flags.add_mapping",
                    "flagId": str(flag_id),
                    "previousRunId": str(context.get("run_id")),
                    "newRunId": new_run["id"] if new_run else None,
                },
            )
        return Response({"mapping": after_mapping, "flag": after_flag, "reconciliationRun": new_run})


def _review_flag(request, flag_id: str, *, action: str):
    if not has_request_certs_perm(request, RECONCILIATION_FORM_ID, RECONCILIATION_REVIEW_PROCESS_ID):
        return Response({"detail": "You do not have access to review reconciliation flags."}, status=status.HTTP_403_FORBIDDEN)
    if not is_reconciliation_reviewer(request.user):
        return Response({"detail": "Only Marine Sup'tt or DPA may review reconciliation flags."}, status=status.HTTP_403_FORBIDDEN)
    reason = str(request.data.get("reason") or "").strip()
    if len(reason) < 10:
        return Response({"reason": "Reason must be at least 10 characters."}, status=status.HTTP_400_BAD_REQUEST)
    context = repository.get_flag_context(flag_id)
    if context is None:
        return Response({"detail": "Reconciliation flag not found."}, status=status.HTTP_404_NOT_FOUND)
    if not user_can_access_vessel(request.user, str(context.get("vessel_id"))):
        return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
    with transaction.atomic():
        reviewed = repository.review_flag(flag_id, actor_id=resolve_actor_id(request.user), action=action)
        if reviewed is None or reviewed.get("after") is None:
            return Response({"detail": "Reconciliation flag not found."}, status=status.HTTP_404_NOT_FOUND)
        serialized_before = serialize_reconciliation_flag(reviewed["before"])
        serialized_after = serialize_reconciliation_flag(reviewed["after"])
        run = reviewed.get("run") or {}
        record_audit_event(
            actor=request.user,
            action="reconciliation_review",
            entity_type="reconciliation_flag",
            entity_id=serialized_after["id"],
            vessel_id=str(run.get("vessel_id") or context.get("vessel_id")),
            before=serialized_before,
            after=serialized_after,
            reason=reason,
            metadata={
                "source": "api.certs.reconciliation.flags",
                "resolution_action": action,
                "run_id": serialized_after["runId"],
            },
        )
    return Response(serialized_after)


def _message_vessel_id(request) -> str | None:
    requested = str(request.query_params.get("vesselId") or "").strip()
    if requested:
        return requested
    user_vessel = str(getattr(request.user, "vessel_id", "") or "").strip()
    return user_vessel or None


def _positive_int(value, default: int) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        return default
    return max(parsed, 1)
