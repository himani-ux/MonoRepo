"""
CAR report export views.

Source: BACKEND_STRUCTURE.md Section 10.5
Implements: PRD.md FEAT-RPT-001
"""

import uuid

from django.db import connection
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import RoleCodes
from apps.inspection.deficiency_models import CAR
from core.db_utils import car_vessel_name_annotation
from .evidence_links import build_report_evidence_url
from .serializers import CARDetailSerializer
from .reports import generate_car_pdf


def _lookup_vessel_name(vessel_id) -> str:
    """Lookup vessel name directly from VesselData as a fallback."""
    if not vessel_id:
        return ''
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 vessel_name
                FROM VesselData
                WHERE id = CAST(%s AS uniqueidentifier)
                  AND is_active = 1
                  AND is_deleted = 0
                """,
                [str(vessel_id)],
            )
            row = cursor.fetchone()
            return str(row[0]) if row and row[0] else ''
    except Exception:
        return ''


def _normalize_uuid_text(value) -> str | None:
    """Normalize UUID-like values for safe equality checks."""
    if value is None:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


class CARExportPDFView(APIView):
    """
    GET /api/psc/cars/{id}/export-pdf/

    Generate and download a PDF report for a CAR.
    Returns the PDF as a file download.

    Source: BACKEND_STRUCTURE.md Section 10.5
    Implements: PRD.md FEAT-RPT-001
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        audience = (request.query_params.get('audience') or 'internal').strip().lower()
        if audience not in {'internal', 'external'}:
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'message': "Invalid audience. Use 'internal' or 'external'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            car = CAR.objects.select_related(
                'deficiency__inspection'
            ).prefetch_related(
                'corrective_actions',
                'evidence',
                'clc_mappings',
                'physical_verifications',
            ).annotate(
                vessel_name=car_vessel_name_annotation(),
            ).get(id=id, is_deleted=False)
        except CAR.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Vessel-scope guard: vessel-role users can only export their own vessel's CARs.
        # Use role first (more stable than user_type claim), with UUID normalization.
        user = request.user
        user_role = str(getattr(user, 'role', '') or '').strip()
        user_type = str(getattr(user, 'user_type', '') or '').strip().upper()
        is_vessel_role = user_role in RoleCodes.VESSEL_ROLES
        if not user_role and user_type == 'VESSEL':
            is_vessel_role = True

        if is_vessel_role:
            user_vessel_id = _normalize_uuid_text(getattr(user, 'vessel_id', None))
            car_vessel_id = _normalize_uuid_text(
                getattr(
                    getattr(getattr(car, 'deficiency', None), 'inspection', None),
                    'vessel_id',
                    None,
                )
            )
            if not user_vessel_id or not car_vessel_id or user_vessel_id != car_vessel_id:
                return Response({
                    'error': 'FORBIDDEN',
                    'detail': 'You do not have permission to export this CAR.'
                }, status=status.HTTP_403_FORBIDDEN)

        # Serialize CAR detail data (same as CARDetailView)
        serializer = CARDetailSerializer(car, context={'request': request})
        car_data = serializer.data
        for evidence_item in car_data.get('evidence') or []:
            evidence_id = evidence_item.get('id')
            if evidence_id:
                evidence_item['report_preview_url'] = build_report_evidence_url(
                    request,
                    evidence_id=evidence_id,
                    car_id=car.id,
                )
        vessel_name = (getattr(car, 'vessel_name', '') or '').strip()
        if not vessel_name:
            vessel_name = _lookup_vessel_name(
                getattr(getattr(getattr(car, 'deficiency', None), 'inspection', None), 'vessel_id', None)
            )
        if vessel_name:
            inspection = car_data.get('inspection') or {}
            inspection.setdefault('vessel', {})
            inspection['vessel']['name'] = inspection['vessel'].get('name') or vessel_name
            inspection['vessel_name'] = inspection.get('vessel_name') or vessel_name
            car_data['inspection'] = inspection
            car_data['vessel_name'] = car_data.get('vessel_name') or vessel_name
            car_data['vessel'] = car_data.get('vessel') or {}
            car_data['vessel']['name'] = car_data['vessel'].get('name') or vessel_name

        # Generate PDF
        pdf_bytes = generate_car_pdf(car_data, audience=audience)

        # Return as file download
        car_number = car_data.get('car_number', 'CAR')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{car_number.replace('-', '_')}_{timestamp}_Report.pdf"

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response