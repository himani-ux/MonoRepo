"""Audit PDF download endpoints."""

from __future__ import annotations

from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.finding_types import is_nc_finding, is_observation_finding
from apps.inspection.audit.models import AuditDetail, AuditFinding
from apps.inspection.audit.pdf import (
    generate_audit_nc_pdf,
    generate_audit_obs_pdf,
    generate_audit_plan_pdf,
    generate_audit_report_pdf,
)
from apps.inspection.audit.permissions import user_can_access_audit_detail


class AuditPlanPdfView(APIView):
    """GET /api/audit/audits/{id}/pdf/f601/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        audit_detail = _get_audit_detail(id)
        forbidden = _forbidden_if_no_access(request, audit_detail)
        if forbidden:
            return forbidden
        return _pdf_response(generate_audit_plan_pdf(audit_detail, generated_by=request.user))


class AuditReportPdfView(APIView):
    """GET /api/audit/audits/{id}/pdf/f602/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        audit_detail = _get_audit_detail(id)
        forbidden = _forbidden_if_no_access(request, audit_detail)
        if forbidden:
            return forbidden
        return _pdf_response(generate_audit_report_pdf(audit_detail, generated_by=request.user))


class AuditFindingNcPdfView(APIView):
    """GET /api/audit/findings/{id}/pdf/nc/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        finding = _get_finding(id)
        if not is_nc_finding(finding.finding_type):
            return Response(
                {"error": "VALIDATION_ERROR", "message": "Finding is not an NC finding."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        audit_detail = AuditDetail.objects.get(id=finding.audit_detail_id)
        forbidden = _forbidden_if_no_access(request, audit_detail)
        if forbidden:
            return forbidden
        return _pdf_response(generate_audit_nc_pdf(finding, generated_by=request.user))


class AuditFindingObsPdfView(APIView):
    """GET /api/audit/findings/{id}/pdf/obs/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        finding = _get_finding(id)
        if not is_observation_finding(finding.finding_type):
            return Response(
                {"error": "VALIDATION_ERROR", "message": "Finding is not an Observation finding."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        audit_detail = AuditDetail.objects.get(id=finding.audit_detail_id)
        forbidden = _forbidden_if_no_access(request, audit_detail)
        if forbidden:
            return forbidden
        return _pdf_response(generate_audit_obs_pdf(finding, generated_by=request.user))


def _get_audit_detail(id) -> AuditDetail:
    try:
        return AuditDetail.objects.get(id=id)
    except AuditDetail.DoesNotExist as exc:
        raise Http404("Audit not found.") from exc


def _get_finding(id) -> AuditFinding:
    try:
        return AuditFinding.objects.get(id=id)
    except AuditFinding.DoesNotExist as exc:
        raise Http404("Audit finding not found.") from exc


def _forbidden_if_no_access(request, audit_detail: AuditDetail) -> Response | None:
    if user_can_access_audit_detail(request.user, audit_detail):
        return None
    return Response(
        {"error": "FORBIDDEN", "message": "You do not have access to this audit."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _pdf_response(result):
    response = HttpResponse(result.content, content_type=result.content_type)
    response["Content-Disposition"] = f'attachment; filename="{result.file_name}"'
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response
