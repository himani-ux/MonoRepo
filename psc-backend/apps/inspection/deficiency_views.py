"""
Deficiency views per BACKEND_STRUCTURE.md Section 10.4.

Views:
- DeficiencyCreateView: POST /api/psc/inspections/{inspection_id}/deficiencies/
- DeficiencyActionCodeUpdateView: PUT /api/psc/deficiencies/{id}/action-code/
- DeficiencyWorkflowTransitionView: POST /api/psc/deficiencies/{id}/workflow/
- DeficiencyAllocateView: POST /api/psc/deficiencies/{id}/allocate/
- DeficiencyListFilteredView: GET /api/psc/deficiencies/
"""

import math
import uuid
from django.db import connection, transaction
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Inspection, InspectionStatus
from .deficiency_models import Deficiency, DefStatus
from apps.car.models import ActivityHistory
from apps.accounts.models import RoleCodes
from .deficiency_serializers import (
    DeficiencyCreateSerializer,
    DeficiencyDetailSerializer,
    DeficiencyListSerializer,
    DeficiencyActionCodeUpdateSerializer,
    DeficiencyWorkflowTransitionSerializer,
    DeficiencyAllocateSerializer,
    BulkSubmitSerializer,
)
from .permissions import (
    IsAuthenticated,
    HasVesselAccess,
    CanAddDeficiency,
    CanUpdateDeficiencyActionCode,
    IsVesselMaster,
)
from .workflow import (
    validate_transition,
    determine_reviewer,
    classify_rank,
    _normalize_uuid,
    _uuid_match,
    RANK_MASTER,
)



import logging

logger = logging.getLogger(__name__)


def _compact_uuid_text(value):
    """Return UUID in 32-char compact form when possible."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return uuid.UUID(raw).hex
    except (ValueError, TypeError, AttributeError):
        return raw.replace('-', '')


def _resolve_rank_label(rank_value):
    """
    Resolve rank text from master rank UUID or raw text fallback.
    """
    from apps.accounts.utils import get_rank_name_by_id

    rank_name = get_rank_name_by_id(rank_value)
    if rank_name:
        return rank_name

    raw_rank = str(rank_value or "").strip()
    return raw_rank or None


# class DeficiencyCreateView(APIView):
#     permission_classes = [IsAuthenticated, CanAddDeficiency]

#     @transaction.atomic
#     def post(self, request, inspection_id):

#         #  Get inspection safely
#         inspection = get_object_or_404(
#             Inspection,
#             id=inspection_id,
#             is_deleted=False
#         )

#         #  Vessel access check
#         access_permission = HasVesselAccess()
#         if not access_permission.has_object_permission(request, self, inspection):
#             return Response(
#                 {'error': access_permission.message},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         #  Block if marked NO deficiencies
#         if inspection.def_reported == 'NO':
#             return Response(
#                 {'error': 'Cannot add deficiencies — inspection marked as no deficiencies reported.'},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         #  Validate serializer
#         serializer = DeficiencyCreateSerializer(
#             data=request.data,
#             context={'inspection': inspection},
#         )
#         if not serializer.is_valid():
#             return Response(
#                 {'error': 'Validation failed', 'details': serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Create deficiency
#         deficiency = serializer.save(
#             inspection=inspection,
#             created_by=request.user.display_name or request.user.username,
#         )

#         #  Set workflow safely
#         if deficiency.assigned_crew_id:
#             try:
#                 self._set_workflow_fields(deficiency, inspection, request.user)
#             except Exception as e:
#                 logger.error(f"Workflow assignment failed: {e}")

#         # Activity timeline is non-critical for create flow; do not fail request if logging fails.
#         try:
#             ActivityHistory.objects.create(
#                 entity_type='DEFICIENCY',
#                 entity_id=deficiency.id,
#                 vessel_id=inspection.vessel_id,
#                 event_type='DEFICIENCY_ADDED',
#                 event_description=f'Deficiency {deficiency.def_code} added to inspection',
#                 performed_by=str(request.user.id)[:100],
#                 performed_by_name=request.user.display_name or request.user.username,
#             )
#         except Exception:
#             logger.exception(
#                 "Failed to write DEFICIENCY_ADDED activity history for deficiency_id=%s",
#                 deficiency.id,
#             )

#         response_serializer = DeficiencyDetailSerializer(deficiency)

#         return Response(
#             {
#                 'data': response_serializer.data,
#                 'message': 'Deficiency added successfully'
#             },
#             status=status.HTTP_201_CREATED
#         )

#     #  Fully Safe Owner + Reviewer Logic
#     def _set_workflow_fields(self, deficiency, inspection, requesting_user=None):

#         owner_crew_id = str(deficiency.assigned_crew_id).strip()
#         if not owner_crew_id:
#             return

#         try:
#             # Compatibility: if UUID was persisted in older data, resolve it to CrewID.
#             try:
#                 parsed_uuid = str(uuid.UUID(owner_crew_id))
#                 with connection.cursor() as cursor:
#                     cursor.execute(
#                         """
#                         SELECT TOP 1 h.CrewID
#                         FROM HRM501 h
#                         WHERE h.id = %s
#                           AND h.is_deleted = 0
#                         """,
#                         [parsed_uuid],
#                     )
#                     row = cursor.fetchone()
#                 if row and row[0]:
#                     owner_crew_id = str(row[0]).strip()
#             except (ValueError, TypeError, AttributeError):
#                 pass

#             with connection.cursor() as cursor:
#                 cursor.execute("""
#                     SELECT h.id,
#                         h.CrewID,
#                         r.rank_name AS actual_rank_name,
#                         (h.first_name + ' ' + ISNULL(h.surname,'')) AS full_name
#                     FROM HRM501 h
#                     LEFT JOIN master_applied_rank r
#                         ON r.id = h.rank_name
#                     WHERE h.CrewID = %s
#                     AND h.is_deleted = 0
#                 """, [owner_crew_id])

#                 row = cursor.fetchone()

#             if not row:
#                 return

#             owner_id, crew_id, owner_rank_name, full_name = row

#             # Set owner fields
#             deficiency.owner_rank = owner_rank_name
#             deficiency.owner_name = full_name
#             deficiency.def_status = DefStatus.ALLOCATED

#             #  Determine reviewer safely
#             reviewer = self._determine_reviewer_safe(owner_rank_name, inspection.vessel_id)

#             if reviewer:
#                 deficiency.reviewer_crew_id = reviewer.get("id")
#                 deficiency.reviewer_rank = reviewer.get("rank_name")
#                 deficiency.reviewer_name = reviewer.get("full_name")

#             deficiency.save(update_fields=[
#                 'def_status',
#                 'owner_rank',
#                 'owner_name',
#                 'reviewer_crew_id',
#                 'reviewer_rank',
#                 'reviewer_name',
#             ])

#             # 🔔 Notify assigned crew (skip self assign)
#             requester_crew_id = getattr(requesting_user, 'crew_id', None)

#             if not requester_crew_id or str(crew_id) != str(requester_crew_id):
#                 from apps.notifications.signals import notify_def_assigned
#                 notify_def_assigned(
#                     deficiency,
#                     crew_id=crew_id,
#                     vessel_id=str(inspection.vessel_id),
#                 )

#         except Exception as e:
#             logger.error(f"Owner workflow setup failed: {e}")

#     # 🔥 SAFE reviewer determination using RAW SQL
#     def _determine_reviewer_safe(self, rank_name, vessel_id):
#         from .workflow import classify_rank, RANK_2E, RANK_CE, RANK_CO, RANK_OTHER

#         if not rank_name:
#             return None

#         rank_cat = classify_rank(rank_name)

#         if rank_cat == RANK_2E:
#             target_keywords = ['chief engineer', 'c/e']
#         elif rank_cat in (RANK_CE, RANK_CO, RANK_OTHER):
#             target_keywords = ['master', 'captain']
#         else:
#             return None

#         try:
#             where_clauses = []
#             params = [str(vessel_id)]
#             for kw in target_keywords:
#                 where_clauses.append("LOWER(r.rank_name) LIKE %s")
#                 params.append(f"%{kw}%")

#             rank_filter = " OR ".join(where_clauses) or "1=0"

#             with connection.cursor() as cursor:
#                 cursor.execute(
#                     f"""
#                     SELECT TOP 1 h.id,
#                            r.rank_name,
#                            (h.first_name + ' ' + ISNULL(h.surname,'')) AS full_name
#                     FROM HRM501 h
#                     INNER JOIN  Crew_Onboarding_History coh
#                         ON coh.CrewID = h.CrewID
#                     LEFT JOIN master_applied_rank r
#                         ON r.id = h.rank_name
#                     WHERE coh.Vessel = CAST(%s AS uniqueidentifier)
#                       AND coh.SignOffDate IS NULL
#                       AND h.is_deleted = 0
#                       AND coh.is_deleted = 0
#                       AND r.rank_name IS NOT NULL
#                       AND ({rank_filter})
#                     ORDER BY r.rank_name
#                     """,
#                     params,
#                 )

#                 row = cursor.fetchone()

#             if not row:
#                 return None

#             return {
#                 "id": row[0],
#                 "rank_name": row[1],
#                 "full_name": row[2],
#             }

#         except Exception as e:
#             logger.error(f"Reviewer determination failed: {e}")
#             return None
#         # 




class DeficiencyCreateView(APIView):
    permission_classes = [IsAuthenticated, CanAddDeficiency]

    @transaction.atomic
    def post(self, request, inspection_id):
        # 1. Get inspection safely
        inspection = get_object_or_404(Inspection, id=inspection_id, is_deleted=False)

        # 2. Vessel access check
        access_permission = HasVesselAccess()
        if not access_permission.has_object_permission(request, self, inspection):
            return Response({'error': access_permission.message}, status=status.HTTP_403_FORBIDDEN)

        # 3. Block if marked NO deficiencies
        if inspection.def_reported == 'NO':
            return Response(
                {'error': 'Cannot add deficiencies — inspection marked as no deficiencies reported.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Validate and Create deficiency
        serializer = DeficiencyCreateSerializer(
            data=request.data,
            context={'inspection': inspection},
        )
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        deficiency = serializer.save(
            inspection=inspection,
            created_by=request.user.display_name or request.user.username,
        )

        # 5. Workflow assignment - WRAPPED IN SUB-TRANSACTION to prevent poisoning
        if deficiency.assigned_crew_id:
            try:
                # Nested atomic block ensures that if _set_workflow_fields fails,
                # it rolls back only those changes and doesn't break the main POST transaction.
                with transaction.atomic():
                    self._set_workflow_fields(deficiency, inspection, request.user)
            except Exception as e:
                logger.error(f"Workflow assignment failed for deficiency {deficiency.id}: {e}")

        # 6. Activity History - Now safe from "poisoned" transactions
        ActivityHistory.objects.create(
            entity_type='DEFICIENCY',
            entity_id=deficiency.id,
            vessel_id=str(inspection.vessel_id),
            event_type='DEFICIENCY_ADDED',
            event_description=f'Deficiency {deficiency.def_code} added to inspection',
            performed_by=str(request.user.id),
            performed_by_name=request.user.display_name or request.user.username,
        )

        response_serializer = DeficiencyDetailSerializer(deficiency)
        return Response(
            {'data': response_serializer.data, 'message': 'Deficiency added successfully'},
            status=status.HTTP_201_CREATED
        )

    def _set_workflow_fields(self, deficiency, inspection, requesting_user=None):
        owner_crew_id = str(deficiency.assigned_crew_id).strip()
        if not owner_crew_id:
            return

        # Compatibility: if UUID was persisted in older data, resolve it to CrewID.
        try:
            parsed_uuid = str(uuid.UUID(owner_crew_id))
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TOP 1 h.CrewID
                    FROM HRM501 h
                    WHERE h.id = %s
                      AND h.is_deleted = 0
                    """,
                    [parsed_uuid],
                )
                uuid_row = cursor.fetchone()
            if uuid_row and uuid_row[0]:
                owner_crew_id = str(uuid_row[0]).strip()
        except (ValueError, TypeError, AttributeError):
            pass

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT h.id,
                    h.CrewID,
                    COALESCE(r.rank_name, NULLIF(LTRIM(RTRIM(h.rank_name)), '')) AS actual_rank_name,
                    (ISNULL(h.first_name, '') + ' ' + ISNULL(h.surname, '')) AS full_name
                FROM HRM501 h
                LEFT JOIN master_applied_rank r
                    ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
                WHERE h.CrewID = %s
                  AND ISNULL(h.is_active, 1) = 1
                  AND h.is_deleted = 0
                """,
                [owner_crew_id],
            )
            row = cursor.fetchone()

        if not row:
            return

        owner_id, crew_id, owner_rank_name, full_name = row
        deficiency.owner_rank = owner_rank_name
        deficiency.owner_name = full_name
        deficiency.def_status = DefStatus.ALLOCATED

        reviewer = self._determine_reviewer_safe(owner_rank_name, inspection.vessel_id)
        if reviewer:
            deficiency.reviewer_crew_id = _compact_uuid_text(reviewer.get("id"))
            deficiency.reviewer_rank = reviewer.get("rank_name")
            deficiency.reviewer_name = reviewer.get("full_name")

        deficiency.save(update_fields=[
            'def_status', 'owner_rank', 'owner_name', 
            'reviewer_crew_id', 'reviewer_rank', 'reviewer_name'
        ])

        # Notify logic
        requester_crew_id = getattr(requesting_user, 'crew_id', None)
        if not requester_crew_id or str(crew_id) != str(requester_crew_id):
            from apps.notifications.signals import notify_def_assigned
            notify_def_assigned(deficiency, crew_id=crew_id, vessel_id=str(inspection.vessel_id))

    def _determine_reviewer_safe(self, rank_name, vessel_id):
        from .workflow import classify_rank, RANK_2E, RANK_CE, RANK_CO, RANK_OTHER
        if not rank_name: return None

        rank_cat = classify_rank(rank_name)
        if rank_cat == RANK_2E:
            target_keywords = ['chief engineer', 'c/e']
        elif rank_cat in (RANK_CE, RANK_CO, RANK_OTHER):
            target_keywords = ['master', 'captain']
        else:
            return None

        where_clauses = [f"LOWER(COALESCE(r.rank_name, h.rank_name)) LIKE %s" for _ in target_keywords]
        rank_filter = " OR ".join(where_clauses) or "1=0"
        params = [_normalize_uuid(vessel_id)] + [f"%{kw}%" for kw in target_keywords]

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT TOP 1 h.id, COALESCE(r.rank_name, h.rank_name) AS rank_name,
                           (ISNULL(h.first_name,'') + ' ' + ISNULL(h.surname,'')) AS full_name
                    FROM HRM501 h
                    INNER JOIN Crew_Onboarding_History coh ON coh.CrewID = h.CrewID
                    LEFT JOIN master_applied_rank r
                        ON r.id = TRY_CONVERT(uniqueidentifier, h.rank_name)
                    WHERE TRY_CONVERT(uniqueidentifier, coh.Vessel) = CAST(%s AS uniqueidentifier)
                      AND coh.SignOffDate IS NULL
                      AND ISNULL(coh.is_active, 1) = 1
                      AND ISNULL(coh.is_deleted, 0) = 0
                      AND ISNULL(h.is_active, 1) = 1
                      AND h.is_deleted = 0
                      AND COALESCE(r.rank_name, h.rank_name) IS NOT NULL
                      AND ({rank_filter})
                    ORDER BY r.rank_name
                    """,
                    params,
                )
                row = cursor.fetchone()
        except Exception as e:
            logger.error(f"Reviewer determination failed for vessel {vessel_id}: {e}")
            return None

        return {"id": row[0], "rank_name": row[1], "full_name": row[2]} if row else None



class DeficiencyActionCodeUpdateView(APIView):
    """
    Update deficiency action code with history tracking.

    PUT /api/psc/deficiencies/{id}/action-code/

    Per BACKEND_STRUCTURE.md Section 10.4:
    - Roles: VESSEL_MASTER
    - Creates DeficiencyActionHistory record
    """
    permission_classes = [IsAuthenticated, CanUpdateDeficiencyActionCode]

    def put(self, request, id):
        # Get deficiency
        deficiency = get_object_or_404(
            Deficiency,
            id=id,
            is_deleted=False
        )

        # Check vessel access via inspection
        access_permission = HasVesselAccess()
        if not access_permission.has_object_permission(request, self, deficiency.inspection):
            return Response(
                {'error': access_permission.message},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and update
        serializer = DeficiencyActionCodeUpdateSerializer(
            instance=deficiency,
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update deficiency
        deficiency = serializer.save()

        # Return updated deficiency
        response_serializer = DeficiencyDetailSerializer(deficiency)
        return Response(
            {
                'data': response_serializer.data,
                'message': 'Action code updated'
            },
            status=status.HTTP_200_OK
        )


class DeficiencyWorkflowTransitionView(APIView):
    """
    Transition a deficiency through the vessel-side workflow.

    POST /api/psc/deficiencies/{id}/workflow/
    Body: { target_status: DefStatus, comment?: string }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        deficiency = get_object_or_404(Deficiency, id=id, is_deleted=False)

        # Check vessel access
        access_permission = HasVesselAccess()
        if not access_permission.has_object_permission(request, self, deficiency.inspection):
            return Response(
                {'error': access_permission.message},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DeficiencyWorkflowTransitionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_status = serializer.validated_data['target_status']
        comment = serializer.validated_data.get('comment', '')

        # Validate transition
        is_valid, error_msg = validate_transition(
            deficiency.def_status, target_status, request.user, deficiency,
        )
        if not is_valid:
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = deficiency.def_status
        deficiency.def_status = target_status
        deficiency.updated_by = request.user.display_name or request.user.username
        deficiency.save(update_fields=['def_status', 'updated_by', 'updated_date'])

        # Log activity
        ActivityHistory.objects.create(
            entity_type='DEFICIENCY',
            entity_id=deficiency.id,
            vessel_id=deficiency.inspection.vessel_id,
            event_type=f'DEF_{target_status}',
            event_description=(
                f'Deficiency {deficiency.def_code} transitioned from '
                f'{old_status} to {target_status}'
                + (f': {comment}' if comment else '')
            ),
            performed_by=str(request.user.id),
            performed_by_name=request.user.display_name or request.user.username,
        )

        # If SUBMITTED and DEF has a CAR, also set car.status = SUBMITTED
        if target_status == DefStatus.SUBMITTED and deficiency.car:
            deficiency.car.status = 'SUBMITTED'
            deficiency.car.save(update_fields=['status'])

        response_serializer = DeficiencyDetailSerializer(deficiency)
        return Response(
            {
                'data': response_serializer.data,
                'message': f'Deficiency transitioned to {target_status}',
            },
            status=status.HTTP_200_OK,
        )


class DeficiencyAllocateView(APIView):
    """
    Allocate a deficiency to a crew member (Master only).

    POST /api/psc/deficiencies/{id}/allocate/
    Body: { assigned_crew_id: CrewID, reviewer_crew_id?: UUID }
    """
    permission_classes = [IsAuthenticated, IsVesselMaster]

    def post(self, request, id):
        deficiency = get_object_or_404(Deficiency, id=id, is_deleted=False)

        # Check vessel access
        access_permission = HasVesselAccess()
        if not access_permission.has_object_permission(request, self, deficiency.inspection):
            return Response(
                {'error': access_permission.message},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DeficiencyAllocateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.accounts.models import HRM501

        assigned_crew_id = serializer.validated_data['assigned_crew_id']
        reviewer_crew_id = serializer.validated_data.get('reviewer_crew_id')

        # Look up owner by CrewID
        owner = HRM501.objects.filter(
            CrewID=assigned_crew_id,
            is_deleted=0,
        ).first()

        if not owner:
            return Response(
                {'error': 'Assigned crew member not found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        owner_rank_name = _resolve_rank_label(owner.rank_name)
        deficiency.assigned_crew_id = assigned_crew_id
        deficiency.owner_rank = owner_rank_name
        deficiency.owner_name = owner.full_name or assigned_crew_id
        deficiency.def_status = DefStatus.ALLOCATED

        # Determine reviewer
        if reviewer_crew_id:
            # Manual override
            reviewer_uid = _normalize_uuid(reviewer_crew_id)
            reviewer = HRM501.objects.extra(
                where=["id = CAST(%s AS uniqueidentifier)", "is_deleted = 0"],
                params=[reviewer_uid],
            ).first()
            if reviewer:
                deficiency.reviewer_crew_id = _compact_uuid_text(reviewer.id)
                deficiency.reviewer_rank = _resolve_rank_label(reviewer.rank_name)
                deficiency.reviewer_name = reviewer.full_name or str(reviewer.id)
        else:
            # Auto-determine
            reviewer, _ = determine_reviewer(
                owner_rank_name,
                str(deficiency.inspection.vessel_id),
            )
            if reviewer:
                deficiency.reviewer_crew_id = _compact_uuid_text(reviewer.id)
                deficiency.reviewer_rank = _resolve_rank_label(reviewer.rank_name)
                deficiency.reviewer_name = reviewer.full_name or str(reviewer.id)

        deficiency.updated_by = request.user.display_name or request.user.username
        deficiency.save()

        # Log activity
        ActivityHistory.objects.create(
            entity_type='DEFICIENCY',
            entity_id=deficiency.id,
            vessel_id=deficiency.inspection.vessel_id,
            event_type='DEF_ALLOCATED',
            event_description=(
                f'Deficiency {deficiency.def_code} allocated to '
                f'{owner_rank_name} - {owner.full_name}'
            ),
            performed_by=str(request.user.id),
            performed_by_name=request.user.display_name or request.user.username,
        )

        # Notify the assigned crew member (skip if assigning to self)
        requester_crew_id = getattr(request.user, 'crew_id', None)
        if not requester_crew_id or str(owner.CrewID) != str(requester_crew_id):
            from apps.notifications.signals import notify_def_assigned
            notify_def_assigned(
                deficiency,
                crew_id=owner.CrewID,
                vessel_id=str(deficiency.inspection.vessel_id),
            )

        response_serializer = DeficiencyDetailSerializer(deficiency)
        return Response(
            {
                'data': response_serializer.data,
                'message': 'Deficiency allocated successfully',
            },
            status=status.HTTP_200_OK,
        )


class DeficiencyListFilteredView(APIView):
    """
    List deficiencies with filters, scoped to user's vessel.

    GET /api/psc/deficiencies/?status=X&owner=Y&awaiting_review=true
    Returns paginated {data, pagination} format.
    """
    permission_classes = [IsAuthenticated]

    DEFAULT_PAGE_SIZE = 20

    def get(self, request):
        user = request.user

        # Vessel users: scope to own vessel
        if user.user_type == 'VESSEL' and user.vessel_id:
            qs = Deficiency.objects.filter(
                inspection__vessel_id=user.vessel_id,
                is_deleted=False,
            ).select_related('inspection', 'car')

            # Crew members can only see deficiencies assigned to them
            if user.role == 'VESSEL_CREW':
                from django.db.models import Q
                qs = qs.filter(
                    Q(assigned_crew_id=user.crew_id) |
                    Q(assigned_crew_id=user.id)
                )
        elif user.user_type == 'OFFICE':
            from core.vessel_access import apply_office_vessel_filter
            from .deficiency_models import CARStatus
            qs = Deficiency.objects.filter(is_deleted=False).select_related(
                'inspection', 'car',
            )
            if user.role in RoleCodes.PIC_REVIEWERS:
                # Keep existing vessel-scoped access, but always include PIC inbox items
                # so role-forwarded deficiencies are visible for PIC review.
                scoped_qs = apply_office_vessel_filter(qs, user, 'inspection__vessel_id')
                pic_inbox_qs = qs.filter(car__status__in=[
                    CARStatus.SUBMITTED_TO_PIC,
                    CARStatus.PIC_REVIEW,
                ])
                qs = (scoped_qs | pic_inbox_qs).distinct()
            elif user.role == RoleCodes.DPA:
                # DPA inbox starts only after PIC submits to DPA.
                qs = qs.filter(car__status__in=[
                    CARStatus.SUBMITTED_TO_DPA,
                    CARStatus.CLOSED,
                ])
            else:
                qs = apply_office_vessel_filter(qs, user, 'inspection__vessel_id')
        else:
            return Response(
                {'error': 'Cannot determine vessel access.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Apply filters
        def_status = request.query_params.get('status')
        if def_status:
            qs = qs.filter(def_status=def_status)

        # Filter by CAR status (new unified workflow)
        car_status = request.query_params.get('car_status')
        if car_status:
            qs = qs.filter(car__status=car_status)

        owner = request.query_params.get('owner')
        if owner:
            qs = qs.filter(assigned_crew_id=owner)

        awaiting_review = request.query_params.get('awaiting_review')
        if awaiting_review and awaiting_review.lower() == 'true':
            qs = qs.filter(def_status__in=[
                DefStatus.COMPLETED,
                DefStatus.UNDER_REVIEW,
            ])

        def_code = request.query_params.get('def_code')
        if def_code:
            qs = qs.filter(def_code_id=def_code)

        vessel_id = request.query_params.get('vessel_id')
        if vessel_id:
            try:
                vessel_uuid = uuid.UUID(vessel_id)
            except (ValueError, AttributeError):
                return Response(
                    {'error': 'Invalid vessel_id parameter'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(inspection__vessel_id=vessel_uuid)

        date_from = request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(inspection__inspection_date__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(inspection__inspection_date__lte=date_to)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', self.DEFAULT_PAGE_SIZE))
        total = qs.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        offset = (page - 1) * page_size
        deficiencies = qs.order_by('-created_date')[offset:offset + page_size]

        serializer = DeficiencyListSerializer(deficiencies, many=True)
        return Response({
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total,
                'total_pages': total_pages,
            },
        })


class BulkDeficiencySubmitView(APIView):
    """
    Bulk-submit multiple APPROVED deficiencies to the office.

    POST /api/psc/inspections/{inspection_id}/deficiencies/bulk-submit/
    Body: { deficiency_ids: [uuid, ...], comment?: string }
    """
    permission_classes = [IsAuthenticated, IsVesselMaster]

    def post(self, request, inspection_id):
        inspection = get_object_or_404(Inspection, id=inspection_id, is_deleted=False)

        # Check vessel access
        access_permission = HasVesselAccess()
        if not access_permission.has_object_permission(request, self, inspection):
            return Response(
                {'error': access_permission.message},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BulkSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ids = serializer.validated_data['deficiency_ids']
        comment = serializer.validated_data.get('comment', '')

        deficiencies = Deficiency.objects.filter(
            id__in=ids, inspection_id=inspection_id, is_deleted=False,
        ).select_related('car')

        # Ensure all requested IDs were found
        if deficiencies.count() != len(ids):
            found_ids = set(str(d.id) for d in deficiencies)
            missing = [str(i) for i in ids if str(i) not in found_ids]
            return Response(
                {'error': f'Deficiencies not found: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure all have CAR in PENDING_MASTER_REVIEW status
        non_ready = [d for d in deficiencies
                     if not d.car or d.car.status != 'PENDING_MASTER_REVIEW']
        if non_ready:
            codes = ', '.join(d.def_code for d in non_ready)
            return Response(
                {'error': f'Deficiencies not ready for submission (CAR must be Pending Master Review): {codes}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        performer = request.user.display_name or request.user.username
        activity_entries = []

        with transaction.atomic():
            for d in deficiencies:
                d.def_status = DefStatus.SUBMITTED
                d.updated_by = performer
                d.save(update_fields=['def_status', 'updated_by', 'updated_date'])

                if d.car:
                    d.car.status = 'SUBMITTED_TO_PIC'
                    d.car.save(update_fields=['status'])

                activity_entries.append(ActivityHistory(
                    entity_type='DEFICIENCY',
                    entity_id=d.id,
                    vessel_id=inspection.vessel_id,
                    event_type='DEF_SUBMITTED',
                    event_description=(
                        f'Deficiency {d.def_code} submitted to office (bulk submit)'
                        + (f': {comment}' if comment else '')
                    ),
                    performed_by=str(request.user.id),
                    performed_by_name=performer,
                ))

            ActivityHistory.objects.bulk_create(activity_entries)

        # Refresh from DB for response
        deficiencies = Deficiency.objects.filter(
            id__in=ids,
        ).select_related('car')
        response_serializer = DeficiencyDetailSerializer(deficiencies, many=True)

        return Response(
            {
                'data': response_serializer.data,
                'message': f'{len(ids)} deficiencies submitted successfully.',
            },
            status=status.HTTP_200_OK,
        )