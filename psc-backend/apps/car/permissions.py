"""
CAR permission classes per BACKEND_STRUCTURE.md Section 11 (RBAC).

Permission classes for:
- CAR state transitions (edit, submit, PIC accept, rework, DPA close)
- Evidence management (upload, delete)
- Corrective actions (add, update, complete)
- Physical verification (create, close)
"""

from rest_framework import permissions

from apps.accounts.models import RoleCodes
from apps.inspection.deficiency_models import CARStatus
from .models import CorrectiveAction


# Roles that can perform PIC-level review actions
PIC_REVIEWER_ROLES = [
    RoleCodes.OFFICE_PIC,
    RoleCodes.OFFICE_SSQE,
    RoleCodes.OFFICE_SUPT,
]

# Roles that can manage CAR content (vessel master + all office)
CAR_MANAGER_ROLES = [
    RoleCodes.VESSEL_MASTER,
    RoleCodes.OFFICE_PIC,
    RoleCodes.OFFICE_SSQE,
    RoleCodes.OFFICE_SUPT,
    RoleCodes.DPA,
]


import uuid
from rest_framework.permissions import BasePermission

class CanEditCAR(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        # OFFICE can edit anything
        if request.user.user_type == 'OFFICE':
            return True

        if request.user.user_type == 'VESSEL':

            car_vessel_id = obj.deficiency.inspection.vessel_id
            user_vessel_id = request.user.vessel_id

            # Safe UUID comparison
            try:
                if uuid.UUID(str(car_vessel_id)) != uuid.UUID(str(user_vessel_id)):
                    return False
            except Exception:
                return False

            # Status restriction
            if obj.status not in ['ALLOTTED', 'IN_PROGRESS','PENDING_CE_REVIEW','PENDING_MASTER_REVIEW']:
                print("CAR STATUS:", obj.status)

                return False
            return True
        return False



class CanSubmitCAR(permissions.BasePermission):
    """
    Permission to submit CAR for PIC review.
    Per BACKEND_STRUCTURE.md: VESSEL_MASTER, OFFICE_*
    Preconditions validated in serializer:
    - root_cause_summary >= 50 chars
    - >= 1 IMMEDIATE action
    - >= 1 LONG_TERM action
    - >= 1 BEFORE evidence
    - >= 1 AFTER evidence
    """
    message = "You don't have permission to submit this CAR."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Must be in ALLOTTED or IN_PROGRESS status (legacy endpoint)
        if obj.status not in (CARStatus.ALLOTTED, CARStatus.IN_PROGRESS,
                               CARStatus.PENDING_MASTER_REVIEW):
            self.message = "Only CARs in editable status can be submitted."
            return False

        # Check role
        if request.user.role not in CAR_MANAGER_ROLES:
            return False

        # Vessel user can only submit for their own vessel
        if request.user.user_type == 'VESSEL':
            deficiency = getattr(obj, 'deficiency', None)
            if deficiency:
                inspection = deficiency.inspection
                if str(inspection.vessel_id) != request.user.vessel_id:
                    self.message = "You can only submit CARs for your own vessel."
                    return False

        return True


class CanPICAcceptCAR(permissions.BasePermission):
    """
    Permission to PIC accept a CAR.
    Per BACKEND_STRUCTURE.md: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
    Precondition: status = SUBMITTED
    """
    message = "You don't have permission to accept this CAR."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role not in PIC_REVIEWER_ROLES:
            self.message = "Only PIC, SSQE, or SUPT can accept CARs."
            return False

        if obj.status != CARStatus.SUBMITTED_TO_PIC:
            self.message = "Only submitted CARs can be accepted."
            return False

        return True


class CanRequestRework(permissions.BasePermission):
    """
    Permission to request rework on a CAR.
    Per BACKEND_STRUCTURE.md: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, DPA
    Precondition: status = SUBMITTED or PIC_ACCEPTED
    """
    message = "You don't have permission to request rework on this CAR."

    ALLOWED_ROLES = PIC_REVIEWER_ROLES + [RoleCodes.DPA]
    ALLOWED_STATUSES = [CARStatus.SUBMITTED_TO_PIC, CARStatus.PIC_REVIEW, CARStatus.SUBMITTED_TO_DPA]

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role not in self.ALLOWED_ROLES:
            self.message = "Only Office PIC/SSQE/SUPT or DPA can request rework."
            return False

        if obj.status not in self.ALLOWED_STATUSES:
            self.message = "Rework can only be requested for submitted or PIC-accepted CARs."
            return False

        return True


class CanDPACloseCAR(permissions.BasePermission):
    """
    Permission to DPA close a CAR.
    Per BACKEND_STRUCTURE.md: DPA only
    Precondition: status = SUBMITTED_TO_DPA
    """
    message = "You don't have permission to close this CAR."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role != RoleCodes.DPA:
            self.message = "Only DPA can close CARs."
            return False

        if obj.status != CARStatus.SUBMITTED_TO_DPA:
            self.message = "Only CARs submitted to DPA can be closed."
            return False

        return True


class CanReopenCAR(permissions.BasePermission):
    """
    Permission to reopen a closed CAR (triggers rework).
    Per BACKEND_STRUCTURE.md: DPA only
    Precondition: status = DPA_CLOSED
    """
    message = "You don't have permission to reopen this CAR."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role != RoleCodes.DPA:
            self.message = "Only DPA can reopen CARs."
            return False

        if obj.status != CARStatus.CLOSED:
            self.message = "Only closed CARs can be reopened."
            return False

        return True


class CanUploadEvidence(permissions.BasePermission):
    """
    Permission to upload evidence to a CAR.
    Per FEAT-CAR-003 gap fix:
    - OFFICE users and VESSEL_MASTER can upload
    - VESSEL_CREW can upload only when assignment constraints pass
    """
    message = "You must be authenticated to upload evidence."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Office users and vessel master are always allowed
        if request.user.user_type == 'OFFICE' or request.user.role == RoleCodes.VESSEL_MASTER:
            return True

        # Crew uploads are constrained by corrective-action assignments
        if request.user.role != RoleCodes.VESSEL_CREW:
            self.message = "You don't have permission to upload evidence."
            return False

        crew_id = getattr(request.user, 'crew_id', None)
        if not crew_id:
            self.message = "Crew assignment is required to upload evidence."
            return False

        assigned_crew_ids = CorrectiveAction.objects.filter(
            car=obj,
            is_deleted=False,
            owner_crew_id__isnull=False,
        ).values_list('owner_crew_id', flat=True).distinct()

        # If no crew-specific assignments exist, allow upload.
        if not assigned_crew_ids:
            return True

        if any(str(owner_crew_id) == str(crew_id) for owner_crew_id in assigned_crew_ids):
            return True

        self.message = "You can only upload evidence for actions assigned to you."
        return False


class CanDeleteEvidence(permissions.BasePermission):
    """
    Permission to delete evidence.
    Per BACKEND_STRUCTURE.md: VESSEL_MASTER, OFFICE_*
    """
    message = "You don't have permission to delete evidence."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Align with upload behavior so users who can upload can also remove
        # mistaken files in edit flow.
        return (
            request.user.role in CAR_MANAGER_ROLES
            or request.user.role == RoleCodes.VESSEL_CREW
        )


class CanManageAction(permissions.BasePermission):
    """
    Permission to add/update corrective actions.
    VESSEL_MASTER, VESSEL_CREW (assigned), OFFICE_*
    """
    message = "You don't have permission to manage corrective actions."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in CAR_MANAGER_ROLES:
            return True
        # Crew can manage actions (object-level check in CanEditCAR ensures assignment)
        if request.user.role == RoleCodes.VESSEL_CREW:
            return True
        return False


class CanCompleteAction(permissions.BasePermission):
    """
    Permission to mark a corrective action as completed.
    Per BACKEND_STRUCTURE.md:
    - VESSEL_MASTER: any action
    - VESSEL_CREW: own actions only
    - OFFICE_*: any action
    """
    message = "You don't have permission to complete this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # All office users can complete any action
        if request.user.user_type == 'OFFICE':
            return True

        # Vessel master can complete any action
        if request.user.role == RoleCodes.VESSEL_MASTER:
            return True

        # Vessel crew can complete (object-level check later)
        if request.user.role == RoleCodes.VESSEL_CREW:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Office and vessel master already passed has_permission
        if request.user.user_type == 'OFFICE' or request.user.role == RoleCodes.VESSEL_MASTER:
            return True

        # Vessel crew can only complete their own actions
        if request.user.role == RoleCodes.VESSEL_CREW:
            # Check if crew is the owner
            if obj.owner_crew_id and str(obj.owner_crew_id) == request.user.crew_id:
                return True
            self.message = "You can only complete your own assigned actions."
            return False

        return False


class CanCreatePV(permissions.BasePermission):
    """
    Permission to create physical verification.
    Per BACKEND_STRUCTURE.md: OFFICE_*, DPA
    Precondition: CAR status = DPA_CLOSED (checked in view)
    """
    message = "You don't have permission to create physical verifications."

    ALLOWED_ROLES = [
        RoleCodes.OFFICE_PIC,
        RoleCodes.OFFICE_SSQE,
        RoleCodes.OFFICE_SUPT,
        RoleCodes.DPA,
    ]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in self.ALLOWED_ROLES


class CanClosePV(permissions.BasePermission):
    """
    Permission to close a physical verification.
    Per BACKEND_STRUCTURE.md: Assigned verifier or DPA
    """
    message = "You don't have permission to close this physical verification."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # DPA can close any PV
        if request.user.role == RoleCodes.DPA:
            return True

        # Assigned verifier can close
        user_id = getattr(request.user, 'employee_id', None) or getattr(request.user, 'username', None)
        if obj.verifier_user_id and obj.verifier_user_id == user_id:
            return True

        self.message = "Only the assigned verifier or DPA can close this verification."
        return False
