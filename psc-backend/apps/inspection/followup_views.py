"""
PSC Follow-up views — same-inspection follow-up wizard.

Endpoints:
- POST /api/psc/inspections/<inspection_id>/follow-up/ (canonical)
- POST /api/psc/psc-follow-up/register/ (legacy alias)
"""

import json
import os
import uuid as uuid_lib

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .followup_serializers import FollowUpSerializer
from .models import Inspection, InspectionReport
from .serializers import InspectionDetailSerializer
from .deficiency_models import Deficiency, DeficiencyActionHistory
from .permissions import IsVesselMaster, HasVesselAccess
from apps.car.models import ActivityHistory
from apps.masters.models import PSCActionCode
from apps.notifications.signals import notify_psc_follow_up_recorded
from core.db_utils import vessel_name_annotation, vessel_code_annotation, imo_number_annotation
from django.db.models.expressions import RawSQL


REPORT_FILE_NAME_MAX_LENGTH = 255
REPORT_DESCRIPTION_MAX_LENGTH = 500
REPORT_MIME_TYPE_MAX_LENGTH = 100
REPORT_EXTENSION_MAX_LENGTH = 20
AUDIT_USER_ID_MAX_LENGTH = 100
AUDIT_USER_NAME_MAX_LENGTH = 200
ACTION_CHANGE_REASON_MAX_LENGTH = 500
ACTIVITY_DESCRIPTION_MAX_LENGTH = 500
FOLLOW_UP_DEFICIENCY_MARKER_PREFIX = '[CAR_DEFICIENCIES:'


def _truncate_text(value, max_length):
    text = str(value or '').strip()
    return text[:max_length]


def _truncate_file_name(file_name, max_length=REPORT_FILE_NAME_MAX_LENGTH):
    clean_name = os.path.basename(str(file_name or 'follow-up.pdf')).strip() or 'follow-up.pdf'
    if len(clean_name) <= max_length:
        return clean_name

    stem, ext = os.path.splitext(clean_name)
    ext = ext[: min(len(ext), 20)]
    stem_length = max_length - len(ext)
    return f"{stem[:stem_length]}{ext}" if stem_length > 0 else clean_name[:max_length]


def _append_deficiency_marker(description, deficiencies):
    deficiency_ids = ','.join(str(deficiency.id).replace('-', '') for deficiency in deficiencies)
    marker = f" {FOLLOW_UP_DEFICIENCY_MARKER_PREFIX}{deficiency_ids}]"
    if len(marker) >= REPORT_DESCRIPTION_MAX_LENGTH:
        return _truncate_text(description, REPORT_DESCRIPTION_MAX_LENGTH)

    visible_description = description or 'Follow-up report'
    visible_max_length = REPORT_DESCRIPTION_MAX_LENGTH - len(marker)
    return f"{_truncate_text(visible_description, visible_max_length)}{marker}"


class FollowUpView(APIView):
    """
    POST /api/psc/inspections/<inspection_id>/follow-up/

    Same-inspection follow-up wizard:
    1. Batch-update deficiency action codes
    2. Optionally upload a follow-up report (PDF, max 5MB)
    3. Record activity history event with reinspection_date

    Accepts multipart/form-data:
    - deficiency_updates: JSON string (array of {deficiency_id, action_code_id, notes})
    - reinspection_date: date string (YYYY-MM-DD)
    - notes: optional string
    - report_file: optional PDF file
    - report_description: optional when report_file is present

    Roles: VESSEL_MASTER only
    """
    permission_classes = [IsAuthenticated, IsVesselMaster]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, inspection_id):
        inspection = get_object_or_404(Inspection, id=inspection_id, is_deleted=False)

        # Check vessel access
        access_permission = HasVesselAccess()
        if not access_permission.has_object_permission(request, self, inspection):
            return Response(
                {'error': 'FORBIDDEN', 'message': access_permission.message},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse deficiency_updates from form data (JSON string)
        raw_updates = request.data.get('deficiency_updates', '[]')
        if isinstance(raw_updates, str):
            try:
                deficiency_updates = json.loads(raw_updates)
            except json.JSONDecodeError:
                return Response(
                    {'error': 'VALIDATION_ERROR', 'message': 'Invalid JSON in deficiency_updates'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            deficiency_updates = raw_updates

        # Build data dict for serializer
        data = {
            'deficiency_updates': deficiency_updates,
            'reinspection_date': request.data.get('reinspection_date'),
            'notes': request.data.get('notes', ''),
        }

        serializer = FollowUpSerializer(
            data=data,
            context={'request': request, 'inspection': inspection},
        )
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'message': 'Invalid follow-up data',
                    'details': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        user = request.user
        user_id = _truncate_text(user.id, AUDIT_USER_ID_MAX_LENGTH)
        user_name = _truncate_text(
            getattr(user, 'display_name', None) or getattr(user, 'username', user_id),
            AUDIT_USER_NAME_MAX_LENGTH,
        )
        action_changed_by = _truncate_text(user_name, AUDIT_USER_ID_MAX_LENGTH)

        # Optional report file validation
        report_file = request.FILES.get('report_file')
        report_description = str(request.data.get('report_description', '') or '').strip()
        if report_file:
            # Validate PDF type
            if report_file.content_type not in ('application/pdf',):
                return Response(
                    {'error': 'VALIDATION_ERROR', 'message': 'Report must be a PDF file.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Validate max 5MB
            max_size = 5 * 1024 * 1024
            if report_file.size > max_size:
                return Response(
                    {'error': 'VALIDATION_ERROR', 'message': 'Report file exceeds 5MB limit.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            report_description = _truncate_text(
                report_description or 'Follow-up report',
                REPORT_DESCRIPTION_MAX_LENGTH,
            )

        with transaction.atomic():
            # 1. Update deficiency action codes
            updates = validated['deficiency_updates']
            updated_deficiencies = []
            for update_item in updates:
                deficiency = Deficiency.objects.get(
                    id=update_item['deficiency_id'],
                    is_deleted=False,
                )
                updated_deficiencies.append(deficiency)
                action_code_id = update_item['action_code_id']
                action_code_obj = PSCActionCode.objects.get(action_code=action_code_id)
                new_action_code = str(action_code_obj.action_code)
                change_reason = update_item.get('notes', '') or 'Updated via follow-up wizard'
                change_reason = _truncate_text(change_reason, ACTION_CHANGE_REASON_MAX_LENGTH)

                # Create action history
                DeficiencyActionHistory.objects.create(
                    deficiency=deficiency,
                    previous_action_code_id=deficiency.action_code_id,
                    previous_action_code=deficiency.action_code,
                    new_action_code_id=action_code_id,
                    new_action_code=new_action_code,
                    follow_up_inspection=inspection,
                    change_reason=change_reason,
                    changed_by=action_changed_by,
                )

                # Update deficiency (do NOT touch is_cleared or CAR.status)
                deficiency.action_code_id = action_code_id
                deficiency.action_code = new_action_code
                deficiency.updated_by = user_id
                deficiency.updated_date = timezone.now()
                deficiency.save(update_fields=[
                    'action_code_id', 'action_code', 'updated_by', 'updated_date',
                ])

            # 2. Optionally save follow-up report
            if report_file:
                safe_original_name = _truncate_file_name(report_file.name)
                file_ext = os.path.splitext(safe_original_name)[1][:REPORT_EXTENSION_MAX_LENGTH]
                unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
                relative_path = (
                    f"psc/{inspection.vessel_id}/inspections/{inspection.id}/{unique_filename}"
                )
                upload_base = (
                    getattr(settings, 'UPLOAD_BASE_PATH', None)
                    or getattr(settings, 'PSC_UPLOAD_PATH', None)
                    or (settings.BASE_DIR / 'uploads')
                )
                full_path = os.path.join(str(upload_base), relative_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                with open(full_path, 'wb+') as destination:
                    for chunk in report_file.chunks():
                        destination.write(chunk)

                marked_report_description = _append_deficiency_marker(
                    report_description,
                    updated_deficiencies,
                )
                InspectionReport.objects.create(
                    inspection=inspection,
                    report_type='FOLLOW_UP',
                    file_name=safe_original_name,
                    file_path=relative_path,
                    file_size=report_file.size,
                    mime_type=_truncate_text(report_file.content_type, REPORT_MIME_TYPE_MAX_LENGTH),
                    description=marked_report_description,
                    uploaded_by=user_id,
                )

            # 3. Activity history event
            reinspection_date = validated['reinspection_date']
            notes = validated.get('notes', '')
            desc_parts = [
                f"Follow-up recorded: {len(updates)} deficiencies updated.",
                f"Reinspection date: {reinspection_date}",
            ]
            if notes:
                desc_parts.append(f"Notes: {notes}")
            ActivityHistory.objects.create(
                entity_type='INSPECTION',
                entity_id=str(inspection.id),
                vessel_id=str(inspection.vessel_id) if inspection.vessel_id else None,
                event_type='PSC_FOLLOW_UP_RECORDED',
                event_description=_truncate_text(' '.join(desc_parts), ACTIVITY_DESCRIPTION_MAX_LENGTH),
                performed_by=user_id,
                performed_by_name=user_name,
            )

        # 4. Send notification
        vessel_id = str(inspection.vessel_id) if inspection.vessel_id else None
        if vessel_id:
            try:
                notify_psc_follow_up_recorded(inspection, vessel_id)
            except Exception:
                pass  # Non-critical

        # 5. Return updated inspection detail (with annotations)
        annotated = Inspection.objects.filter(id=inspection.id).annotate(
            vessel_name=vessel_name_annotation(),
            vessel_code=vessel_code_annotation(),
            imo_number=imo_number_annotation(),
            open_deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0 "
                "AND (d.action_code_id IS NULL OR d.action_code_id != 10))",
                [],
            ),
            closed_deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0 "
                "AND d.action_code_id = 10)",
                [],
            ),
        ).first()

        return Response(
            {
                'data': InspectionDetailSerializer(
                    annotated, context={'request': request}
                ).data,
                'message': 'Follow-up recorded successfully',
            },
            status=status.HTTP_200_OK,
        )


class LegacyFollowUpView(APIView):
    """
    POST /api/psc/psc-follow-up/register/

    Legacy alias — extracts parent_inspection_id from body and delegates
    to the canonical FollowUpView.
    """
    permission_classes = [IsAuthenticated, IsVesselMaster]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        parent_id = request.data.get('parent_inspection_id')
        if not parent_id:
            return Response(
                {'error': 'VALIDATION_ERROR', 'message': 'parent_inspection_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Delegate to canonical view
        view = FollowUpView.as_view()
        request.parser_context['kwargs'] = {'inspection_id': parent_id}
        return view(request, inspection_id=parent_id)
