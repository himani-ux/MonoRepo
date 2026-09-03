from rest_framework.permissions import IsAuthenticated
import logging

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.car.views import CARWorkflowView
from apps.inspection.audit.permissions import CanUseAuditCarWorkflow
from apps.inspection.audit.services.car_workflow import (
    AuditCarWorkflowError,
    apply_successful_audit_car_transition,
    resolve_audit_car_workflow_context,
    validate_audit_proxy_preconditions,
)
from apps.inspection.audit.services.certs_writeback import enqueue_external_close_writebacks
from apps.inspection.audit.services.nc_closure import schedule_effectiveness_review
from apps.inspection.workflow import WorkflowAction


logger = logging.getLogger(__name__)


class AuditFindingCarWorkflowView(APIView):
    """Proxy Audit finding workflow requests through the existing PSC CAR endpoint."""

    permission_classes = [IsAuthenticated, CanUseAuditCarWorkflow]

    def post(self, request, id, *args, **kwargs):
        try:
            context = resolve_audit_car_workflow_context(id)
            validate_audit_proxy_preconditions(
                context,
                action=request.data.get("action"),
                user=request.user,
            )
        except AuditCarWorkflowError as exc:
            return Response(
                {"error": exc.error, "message": str(exc)},
                status=exc.status_code,
            )

        response = CARWorkflowView().post(request, id=context.car.id, *args, **kwargs)
        if response.status_code < 400:
            apply_successful_audit_car_transition(
                context,
                action=request.data.get("action"),
                user=request.user,
            )
        if response.status_code < 400 and request.data.get("action") == WorkflowAction.LEAD_AUDITOR_CLOSE:
            context.car.refresh_from_db()
            schedule_effectiveness_review(
                finding_id=id,
                user=request.user,
                closed_at=context.car.last_action_at,
            )
        if response.status_code < 400 and request.data.get("action") == WorkflowAction.CONFIRM_EXTERNAL_CLOSE:
            try:
                enqueue_external_close_writebacks(
                    audit_detail=context.audit_detail,
                    user=request.user,
                )
            except Exception:
                # External close-out must not block on the Certs writeback path.
                logger.exception("Audit external Certs writeback enqueue failed for audit_detail=%s", context.audit_detail.id)
        return response
