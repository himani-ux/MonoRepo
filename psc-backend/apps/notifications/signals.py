"""
Notification signals and helper functions.

Implements: PRD.md FEAT-NOTIF-001

Notification triggers:
1. CAR_CREATED → Vessel Master (on Deficiency post_save → CAR auto-creation)
2. CAR_SUBMITTED → Office PIC/SSQE (called from CARSubmitView)
3. CAR_SUBMITTED (to DPA) → Office DPA (called from CARWorkflowView SUBMIT_TO_DPA)
4. CAR_PIC_ACCEPTED → Vessel Master (called from CARPICAcceptView)
5. CAR_REWORK_REQUESTED → Vessel Master + Assigned Crew + Action Owners (called from CARReworkView)
6. CAR_DPA_CLOSED → Vessel Master (called from CARDPACloseView)
7. PSC_FOLLOW_UP_RECORDED → Office + Vessel (called from PSCFollowUpRegisterView)
8. CONFLICT_DETECTED → Vessel Master (called from sync push)
9. CONFLICT_RESOLVED → Vessel Master (called from sync resolve)
10. PHYSICAL_VERIFICATION_CREATED → Vessel Master (called from PVCreateView)
11. ACTION_OVERDUE_WARNING → Action Owner + Master (management command)
12. ACTION_OVERDUE → Action Owner + Master + Office (management command)
13. DEF_ASSIGNED → Assigned Crew Member (called from DeficiencyAllocateView/DeficiencyCreateView)
"""

import logging
from typing import Optional

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification, NotificationType, RecipientType

logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_notification(
    recipient_type: str,
    recipient_id: str,
    notification_type: str,
    title: str,
    message: str,
    vessel_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Optional[Notification]:
    """
    Create a single notification record.

    Args:
        recipient_type: 'CREW' or 'OFFICE'
        recipient_id: CrewID or employee_id
        notification_type: One of NotificationType choices
        title: Notification title (max 200 chars)
        message: Notification message (max 500 chars)
        vessel_id: UUID string for vessel-specific notifications
        entity_type: Related entity type (e.g., 'CAR', 'INSPECTION')
        entity_id: UUID string of the related entity

    Returns:
        Created Notification object, or None on error
    """
    try:
        return Notification.objects.create(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            vessel_id=vessel_id,
            notification_type=notification_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    except Exception as e:
        logger.error(f"Failed to create notification: {e}", extra={
            'notification_type': notification_type,
            'recipient_type': recipient_type,
            'recipient_id': recipient_id,
        })
        return None


def _get_vessel_master_crew_ids(vessel_id: str) -> list[str]:
    """
    Get CrewIDs of vessel masters for a given vessel.

    Queries HRM501 for active crew with master-level ranks on the vessel.
    """
    from django.db import connection

    master_ranks = [
        'master', 'captain', 'chief officer', 'chief mate',
        'c/o', 'c/e', 'chief engineer',
    ]

    def _extract_master_ids(rows) -> list[str]:
        master_ids = []
        for crew_id, rank_name in rows:
            if rank_name:
                rank_lower = rank_name.lower()
                if any(mr in rank_lower for mr in master_ranks):
                    master_ids.append(crew_id)
        return master_ids

    uid = str(vessel_id)
    if '-' not in uid and len(uid) == 32:
        uid = f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT h.CrewID, r.rank_name
                FROM HRM501 h
                INNER JOIN Crew_Onboarding_History coh
                    ON coh.CrewID = h.CrewID
                LEFT JOIN master_applied_rank r
                    ON r.id = h.rank_name
                WHERE coh.Vessel = CAST(%s AS uniqueidentifier)
                  AND coh.SignOffDate IS NULL
                  AND coh.is_active = 1
                  AND coh.is_deleted = 0
                  AND h.is_active = 1
                  AND h.is_deleted = 0
                """,
                [uid],
            )
            crew_members = cursor.fetchall()
        return _extract_master_ids(crew_members)
    except Exception as e:
        logger.error(f"Failed to get vessel master crew IDs: {e}")
        return []


def _get_office_users_for_vessel(vessel_id: str, role_codes: list[str] | None = None) -> list[str]:
    """
    Get employee_ids of office users assigned to a vessel.

    Args:
        vessel_id: UUID string of the vessel
        role_codes: Optional list of role codes to filter by (e.g., ['OFFICE_PIC', 'OFFICE_SSQE'])
                   If None, returns all office users assigned to the vessel.
    """
    from apps.accounts.models import MasterRoleByVessel, OfficeUser
    from apps.accounts.backends import PSCAuthenticationBackend

    uid = str(vessel_id)
    if '-' not in uid and len(uid) == 32:
        uid = f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"

    def _normalize_ids(values) -> list[str]:
        return sorted({str(v).strip() for v in values if v})

    # Fast path for environments where direct ORM UUID filtering works.
    user_ids: list[str] = []
    try:
        assignments = MasterRoleByVessel.objects.filter(
            VesselId=uid,
            IsActive=True,
            is_deleted=False,
        ).values_list('UserId', flat=True)
        user_ids = _normalize_ids(assignments)
    except Exception:
        # Fall back to SQL Server-safe query below.
        user_ids = []

    # SQL Server unmanaged-table fallback:
    # TRY_CAST avoids conversion errors from non-UUID values in legacy rows.
    if not user_ids:
        try:
            assignments = MasterRoleByVessel.objects.extra(
                where=[
                    "TRY_CAST(VesselId AS uniqueidentifier) = CAST(%s AS uniqueidentifier)",
                    "IsActive = 1",
                    "is_deleted = 0",
                ],
                params=[uid],
            ).values_list('UserId', flat=True)
            user_ids = _normalize_ids(assignments)
        except Exception as e:
            logger.error(f"Failed to get office users for vessel: {e}")
            return []

    if not role_codes or not user_ids:
        return user_ids

    # Filter by role if specified
    backend = PSCAuthenticationBackend()
    filtered_ids = []
    for user_id in user_ids:
        try:
            office_user = OfficeUser.objects.filter(
                employee_id=user_id,
                is_active=True,
                is_deleted=False,
            ).first()
            if office_user:
                role = backend._determine_office_role(office_user.employee_role)
                if role in role_codes:
                    filtered_ids.append(user_id)
        except Exception:
            continue
    return filtered_ids


def _get_vessel_id_from_car(car) -> Optional[str]:
    """Get vessel_id from a CAR by traversing deficiency -> inspection."""
    try:
        return str(car.deficiency.inspection.vessel_id)
    except (AttributeError, Exception):
        return None


def _get_active_crew_member(owner_id):
    """
    Resolve an active HRM501 crew record by CrewID or UUID.

    Handles both test environments (SQLite, direct UUID compare) and
    SQL Server unmanaged-table lookups (CAST to uniqueidentifier).
    """
    from apps.accounts.models import HRM501

    try:
        # CrewID fast-path
        crew = HRM501.objects.filter(
            CrewID=owner_id,
            is_active=True,
            is_deleted=False,
        ).first()
        if crew:
            return crew

        crew = HRM501.objects.filter(
            id=owner_id,
            is_active=True,
            is_deleted=False,
        ).first()
        if crew:
            return crew
    except Exception:
        pass

    uid = str(owner_id)
    if '-' not in uid and len(uid) == 32:
        uid = f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"

    try:
        return HRM501.objects.extra(
            where=["id = CAST(%s AS uniqueidentifier)", "is_active = 1", "is_deleted = 0"],
            params=[uid],
        ).first()
    except Exception:
        return None


def _get_office_user_ids_for_roles(role_codes: list[str]) -> list[str]:
    """Resolve active office employee IDs whose mapped role is in the requested set."""
    from apps.accounts.backends import PSCAuthenticationBackend
    from apps.accounts.models import OfficeUser

    backend = PSCAuthenticationBackend()
    resolved_ids: list[str] = []
    allowed_roles = set(role_codes or [])

    if not allowed_roles:
        return resolved_ids

    try:
        office_users = OfficeUser.objects.filter(
            is_active=True,
            is_deleted=False,
        ).only('employee_id', 'employee_role')
    except Exception as exc:
        logger.error(f"Failed to load office users for circular notifications: {exc}")
        return resolved_ids

    for office_user in office_users:
        employee_id = str(getattr(office_user, 'employee_id', '') or '').strip()
        if not employee_id:
            continue

        try:
            resolved_role = backend._determine_office_role(office_user.employee_role)
        except Exception:
            continue

        if resolved_role in allowed_roles:
            resolved_ids.append(employee_id)

    return sorted(set(resolved_ids))


def _build_circular_label(sr_no: str, doc_type_name: Optional[str] = None) -> str:
    """Build a user-facing circular label such as 'Circular KSM/...''."""
    sr_value = str(sr_no or '').strip()
    doc_type_value = str(doc_type_name or 'Circular').strip() or 'Circular'
    return f'{doc_type_value} {sr_value}'.strip()


def notify_circular_created(
    *,
    sr_no: str,
    title: Optional[str],
    creator_employee_id: Optional[str],
    notification_id: Optional[str] = None,
    doc_type_name: Optional[str] = None,
):
    """Notify the circular creator that a draft was created."""
    creator_id = str(creator_employee_id or '').strip()
    if not creator_id:
        return

    circular_label = _build_circular_label(sr_no, doc_type_name)
    subject = str(title or sr_no or 'Untitled circular').strip()

    create_notification(
        recipient_type=RecipientType.OFFICE,
        recipient_id=creator_id,
        notification_type=NotificationType.CIRCULAR_CREATED,
        title=f'{circular_label} created',
        message=f'"{subject}" has been saved in Circulars.',
        entity_type='CIRCULAR',
        entity_id=str(notification_id) if notification_id else None,
    )


def notify_circular_pending_approval(
    *,
    sr_no: str,
    title: Optional[str],
    creator_employee_id: Optional[str],
    notification_id: Optional[str] = None,
    doc_type_name: Optional[str] = None,
):
    """Notify the creator and office reviewers that a circular is pending approval."""
    from apps.accounts.models import RoleCodes

    circular_label = _build_circular_label(sr_no, doc_type_name)
    subject = str(title or sr_no or 'Untitled circular').strip()
    creator_id = str(creator_employee_id or '').strip()

    if creator_id:
        create_notification(
            recipient_type=RecipientType.OFFICE,
            recipient_id=creator_id,
            notification_type=NotificationType.CIRCULAR_PENDING_APPROVAL,
            title=f'{circular_label} submitted',
            message=f'"{subject}" has been submitted and is awaiting approval.',
            entity_type='CIRCULAR',
            entity_id=str(notification_id) if notification_id else None,
        )

    reviewer_ids = _get_office_user_ids_for_roles(RoleCodes.PIC_REVIEWERS + RoleCodes.DPA_ROLES)
    for reviewer_id in reviewer_ids:
        if reviewer_id == creator_id:
            continue
        create_notification(
            recipient_type=RecipientType.OFFICE,
            recipient_id=reviewer_id,
            notification_type=NotificationType.CIRCULAR_PENDING_APPROVAL,
            title=f'{circular_label} pending approval',
            message=f'"{subject}" is waiting for review in Circulars.',
            entity_type='CIRCULAR',
            entity_id=str(notification_id) if notification_id else None,
        )


def notify_circular_approved(
    *,
    sr_no: str,
    title: Optional[str],
    creator_employee_id: Optional[str],
    notification_id: Optional[str] = None,
    doc_type_name: Optional[str] = None,
):
    """Notify the creator that a circular has been approved."""
    creator_id = str(creator_employee_id or '').strip()
    if not creator_id:
        return

    circular_label = _build_circular_label(sr_no, doc_type_name)
    subject = str(title or sr_no or 'Untitled circular').strip()

    create_notification(
        recipient_type=RecipientType.OFFICE,
        recipient_id=creator_id,
        notification_type=NotificationType.CIRCULAR_APPROVED,
        title=f'{circular_label} approved',
        message=f'"{subject}" has been approved.',
        entity_type='CIRCULAR',
        entity_id=str(notification_id) if notification_id else None,
    )


def notify_circular_rejected(
    *,
    sr_no: str,
    title: Optional[str],
    creator_employee_id: Optional[str],
    notification_id: Optional[str] = None,
    doc_type_name: Optional[str] = None,
    comment: Optional[str] = None,
):
    """Notify the creator that a circular has been rejected."""
    creator_id = str(creator_employee_id or '').strip()
    if not creator_id:
        return

    circular_label = _build_circular_label(sr_no, doc_type_name)
    subject = str(title or sr_no or 'Untitled circular').strip()
    message = f'"{subject}" has been rejected.'
    trimmed_comment = str(comment or '').strip()
    if trimmed_comment:
        message = f'{message} Comment: {trimmed_comment[:200]}'

    create_notification(
        recipient_type=RecipientType.OFFICE,
        recipient_id=creator_id,
        notification_type=NotificationType.CIRCULAR_REJECTED,
        title=f'{circular_label} rejected',
        message=message,
        entity_type='CIRCULAR',
        entity_id=str(notification_id) if notification_id else None,
    )


def notify_circular_distribution(
    *,
    sr_no: str,
    title: Optional[str],
    crew_ids: list[str],
    notification_id: Optional[str] = None,
    doc_type_name: Optional[str] = None,
):
    """Notify unique crew recipients when an approved circular is distributed to them."""
    circular_label = _build_circular_label(sr_no, doc_type_name)
    subject = str(title or sr_no or 'Untitled circular').strip()
    notified_ids: set[str] = set()

    for crew_id in crew_ids:
        normalized_crew_id = str(crew_id or '').strip()
        if not normalized_crew_id or normalized_crew_id in notified_ids:
            continue

        notified_ids.add(normalized_crew_id)
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=normalized_crew_id,
            notification_type=NotificationType.CIRCULAR_APPROVED,
            title=f'{circular_label} shared with you',
            message=f'"{subject}" has been approved and assigned to you in Circulars.',
            entity_type='CIRCULAR',
            entity_id=str(notification_id) if notification_id else None,
        )


# =============================================================================
# NOTIFICATION TRIGGER FUNCTIONS (called from views)
# =============================================================================

def notify_car_created(car, vessel_id: str):
    """
    CAR_CREATED → Vessel Master.

    Triggered when a CAR is auto-created from a deficiency.
    """
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.CAR_CREATED,
            title=f'CAR {car.car_number} created',
            message=f'CAR {car.car_number} created for deficiency {car.deficiency.def_code}',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )


def notify_car_submitted(car, vessel_id: str):
    """
    CAR_SUBMITTED → Office PIC/SSQE.

    Triggered when a CAR is submitted for review.
    """
    from apps.accounts.models import RoleCodes
    pic_ssqe_ids = _get_office_users_for_vessel(
        vessel_id,
        role_codes=[RoleCodes.OFFICE_PIC, RoleCodes.OFFICE_SSQE],
    )
    for employee_id in pic_ssqe_ids:
        create_notification(
            recipient_type=RecipientType.OFFICE,
            recipient_id=employee_id,
            notification_type=NotificationType.CAR_SUBMITTED,
            title=f'CAR {car.car_number} submitted',
            message=f'CAR {car.car_number} has been submitted for review.',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )


def notify_car_submitted_to_dpa(car, vessel_id: str):
    """
    CAR_SUBMITTED (to DPA) → Office DPA.

    Triggered when PIC submits a CAR to DPA for closure review.
    Uses existing CAR_SUBMITTED notification type for compatibility.
    """
    from apps.accounts.models import RoleCodes

    dpa_ids = _get_office_users_for_vessel(
        vessel_id,
        role_codes=[RoleCodes.DPA],
    )
    for employee_id in dpa_ids:
        create_notification(
            recipient_type=RecipientType.OFFICE,
            recipient_id=employee_id,
            notification_type=NotificationType.CAR_SUBMITTED,
            title=f'CAR {car.car_number} submitted to DPA',
            message=f'CAR {car.car_number} has been submitted to DPA for closure review.',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )


def notify_car_pic_accepted(car, vessel_id: str):
    """
    CAR_PIC_ACCEPTED → Vessel Master.

    Triggered when PIC accepts a CAR.
    """
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.CAR_PIC_ACCEPTED,
            title=f'CAR {car.car_number} accepted',
            message=f'CAR {car.car_number} has been accepted by PIC.',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )


def notify_car_rework_requested(car, vessel_id: str):
    """
    CAR_REWORK_REQUESTED → Vessel Master + Assigned Crew + Action Owners.

    Triggered when rework is requested on a CAR.
    """
    from apps.car.models import CorrectiveAction

    # Notify vessel masters
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.CAR_REWORK_REQUESTED,
            title=f'Rework requested: {car.car_number}',
            message=f'Rework has been requested for CAR {car.car_number}.',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )

    notified_crew = set(master_ids)  # Don't double-notify masters

    # Notify deficiency assignee (primary crew owner of the CAR workflow)
    assigned_crew_id = getattr(getattr(car, 'deficiency', None), 'assigned_crew_id', None)
    if assigned_crew_id:
        assigned_crew = _get_active_crew_member(assigned_crew_id)
        if assigned_crew and assigned_crew.CrewID not in notified_crew:
            notified_crew.add(assigned_crew.CrewID)
            create_notification(
                recipient_type=RecipientType.CREW,
                recipient_id=assigned_crew.CrewID,
                notification_type=NotificationType.CAR_REWORK_REQUESTED,
                title=f'Rework requested: {car.car_number}',
                message=f'CAR {car.car_number} has been returned for rework.',
                vessel_id=vessel_id,
                entity_type='CAR',
                entity_id=str(car.id),
            )

    # Notify action owners (crew members assigned to corrective actions)
    action_owners = CorrectiveAction.objects.filter(
        car=car,
        is_deleted=False,
        owner_crew_id__isnull=False,
    ).values_list('owner_crew_id', flat=True).distinct()

    for owner_id in action_owners:
        if owner_id is None:
            continue
        crew = _get_active_crew_member(owner_id)
        if crew and crew.CrewID not in notified_crew:
            notified_crew.add(crew.CrewID)
            create_notification(
                recipient_type=RecipientType.CREW,
                recipient_id=crew.CrewID,
                notification_type=NotificationType.CAR_REWORK_REQUESTED,
                title=f'Rework requested: {car.car_number}',
                message=f'Rework has been requested for CAR {car.car_number}. Please review your assigned actions.',
                vessel_id=vessel_id,
                entity_type='CAR',
                entity_id=str(car.id),
            )


def notify_car_reopened(car, vessel_id: str):
    """
    CAR_REOPENED → Vessel Master + Action Owners.

    Triggered when DPA reopens a closed CAR.
    """
    from apps.car.models import CorrectiveAction

    # Notify vessel masters
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.CAR_REOPENED,
            title=f'CAR reopened: {car.car_number}',
            message=f'CAR {car.car_number} has been reopened by DPA for further review.',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )

    # Notify action owners (crew members assigned to corrective actions)
    action_owners = CorrectiveAction.objects.filter(
        car=car,
        is_deleted=False,
        owner_crew_id__isnull=False,
    ).values_list('owner_crew_id', flat=True).distinct()

    notified_crew = set(master_ids)  # Don't double-notify masters
    for owner_id in action_owners:
        if owner_id is None:
            continue
        crew = _get_active_crew_member(owner_id)
        if crew and crew.CrewID not in notified_crew:
            notified_crew.add(crew.CrewID)
            create_notification(
                recipient_type=RecipientType.CREW,
                recipient_id=crew.CrewID,
                notification_type=NotificationType.CAR_REOPENED,
                title=f'CAR reopened: {car.car_number}',
                message=f'CAR {car.car_number} has been reopened by DPA. Please review your assigned actions.',
                vessel_id=vessel_id,
                entity_type='CAR',
                entity_id=str(car.id),
            )


def notify_car_dpa_closed(car, vessel_id: str):
    """
    CAR_DPA_CLOSED → Vessel Master.

    Triggered when DPA closes a CAR.
    """
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.CAR_DPA_CLOSED,
            title=f'CAR {car.car_number} closed',
            message=f'CAR {car.car_number} has been closed by DPA.',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )


def notify_inspection_dpa_closed(inspection, vessel_id: str):
    """
    INSPECTION_DPA_CLOSED → Vessel Master.

    Triggered when DPA closes an inspection.
    """
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    if not master_ids:
        fallback_recipient_id = inspection.created_by or vessel_id
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=fallback_recipient_id,
            notification_type=NotificationType.INSPECTION_DPA_CLOSED,
            title='Inspection closed by DPA',
            message=f'Inspection at {inspection.port_place} has been closed by DPA.',
            vessel_id=vessel_id,
            entity_type='INSPECTION',
            entity_id=str(inspection.id),
        )
        return

    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.INSPECTION_DPA_CLOSED,
            title='Inspection closed by DPA',
            message=f'Inspection at {inspection.port_place} has been closed by DPA.',
            vessel_id=vessel_id,
            entity_type='INSPECTION',
            entity_id=str(inspection.id),
        )


def notify_psc_follow_up_recorded(follow_up_inspection, vessel_id: str):
    """
    PSC_FOLLOW_UP_RECORDED → Office + Vessel.

    Triggered when a PSC follow-up inspection is recorded.
    """
    # Notify office users assigned to this vessel
    office_ids = _get_office_users_for_vessel(vessel_id)
    for employee_id in office_ids:
        create_notification(
            recipient_type=RecipientType.OFFICE,
            recipient_id=employee_id,
            notification_type=NotificationType.PSC_FOLLOW_UP_RECORDED,
            title='PSC Follow-up recorded',
            message=f'PSC follow-up inspection recorded at {follow_up_inspection.port_place}.',
            vessel_id=vessel_id,
            entity_type='INSPECTION',
            entity_id=str(follow_up_inspection.id),
        )

    # Notify vessel masters
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.PSC_FOLLOW_UP_RECORDED,
            title='PSC Follow-up recorded',
            message=f'PSC follow-up inspection recorded at {follow_up_inspection.port_place}.',
            vessel_id=vessel_id,
            entity_type='INSPECTION',
            entity_id=str(follow_up_inspection.id),
        )


def notify_conflict_detected(vessel_id: str, entity_type: str, entity_id: str):
    """
    CONFLICT_DETECTED → Vessel Master.

    Triggered when a sync conflict is detected.
    """
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.CONFLICT_DETECTED,
            title='Sync conflict detected',
            message=f'A sync conflict has been detected for {entity_type}. Office will resolve.',
            vessel_id=vessel_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )


def notify_conflict_resolved(vessel_id: str, entity_type: str, entity_id: str, resolution: str):
    """
    CONFLICT_RESOLVED → Vessel Master.

    Triggered when a sync conflict is resolved by office.
    """
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.CONFLICT_RESOLVED,
            title='Sync conflict resolved',
            message=f'Sync conflict for {entity_type} resolved: {resolution}.',
            vessel_id=vessel_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )


def notify_physical_verification_created(pv, car, vessel_id: str):
    """
    PHYSICAL_VERIFICATION_CREATED → Vessel Master.

    Triggered when a physical verification is created.
    """
    master_ids = _get_vessel_master_crew_ids(vessel_id)
    for crew_id in master_ids:
        create_notification(
            recipient_type=RecipientType.CREW,
            recipient_id=crew_id,
            notification_type=NotificationType.PHYSICAL_VERIFICATION_CREATED,
            title=f'Physical verification scheduled: {car.car_number}',
            message=f'Physical verification scheduled for CAR {car.car_number}.',
            vessel_id=vessel_id,
            entity_type='CAR',
            entity_id=str(car.id),
        )


def notify_def_assigned(deficiency, crew_id: str, vessel_id: str):
    """
    DEF_ASSIGNED → Assigned crew member.

    Triggered when a deficiency is allocated to a crew member.
    Includes target date in the message if available.
    """
    target_info = ''
    if deficiency.target_date:
        target_info = f' Target date: {deficiency.target_date.strftime("%d %b %Y")}.'

    create_notification(
        recipient_type=RecipientType.CREW,
        recipient_id=crew_id,
        notification_type=NotificationType.DEF_ASSIGNED,
        title=f'Deficiency {deficiency.def_code} assigned to you',
        message=f'You have been assigned deficiency {deficiency.def_code}.{target_info}',
        vessel_id=vessel_id,
        entity_type='DEFICIENCY',
        entity_id=str(deficiency.id),
    )


# =============================================================================
# DJANGO SIGNAL HANDLERS
# =============================================================================

@receiver(post_save, sender='inspection.CAR')
def on_car_created(sender, instance, created, **kwargs):
    """
    Send CAR_CREATED notification when a CAR is auto-created.

    Hooks into the existing auto_create_car signal flow:
    Deficiency post_save → CAR created → this signal fires.
    """
    if not created:
        return

    car = instance
    vessel_id = _get_vessel_id_from_car(car)
    if vessel_id:
        notify_car_created(car, vessel_id)
