"""
Inspection permissions per BACKEND_STRUCTURE.md Section 11 (RBAC).

Permission classes:
- IsVesselUser: Can only access own vessel
- IsOfficeUser: Can access assigned vessels
- IsDPA: Can access all vessels
- CanCreateInspection: Vessel users and office users
- CanSubmitInspection: Owner in DRAFT status
- CanPICReview: Office PIC/SSQE/SUPT, status = SUBMITTED
- CanDPAClose: DPA only, status = PIC_REVIEWED
"""

from rest_framework import permissions

from apps.accounts.models import RoleCodes


class IsAuthenticated(permissions.BasePermission):
    """Verify user is authenticated."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsVesselUser(permissions.BasePermission):
    """
    Permission for vessel users.
    Can only access data for their own vessel.
    """
    message = "You can only access data for your own vessel."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == 'VESSEL'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.user_type != 'VESSEL':
            return False
        # Check vessel_id matches
        if hasattr(obj, 'vessel_id'):
            return str(obj.vessel_id) == request.user.vessel_id
        return False


class IsOfficeUser(permissions.BasePermission):
    """
    Permission for office users.
    Can access vessels assigned via master_RoleByVessel.
    """
    message = "You don't have access to this vessel's data."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.user_type == 'OFFICE'


class IsDPA(permissions.BasePermission):
    """
    Permission for DPA users.
    Can access all vessels.
    """
    message = "This action requires DPA role."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == RoleCodes.DPA


class IsPICOrHigher(permissions.BasePermission):
    """
    Permission for PIC, SSQE, SUPT, or DPA users.
    """
    message = "This action requires PIC, SSQE, SUPT, or DPA role."

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


class CanCreateInspection(permissions.BasePermission):
    """
    Permission to create inspections.
    Per BACKEND_STRUCTURE.md:
    - PSC and RightShip (RS): VESSEL_MASTER only
    - Other inspection types: VESSEL_MASTER and OFFICE_*
    """
    message = "You don't have permission to create inspections."

    ALLOWED_ROLES = [
        RoleCodes.VESSEL_MASTER,
        RoleCodes.OFFICE_PIC,
        RoleCodes.OFFICE_SSQE,
        RoleCodes.OFFICE_SUPT,
        RoleCodes.DPA,
    ]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        inspection_type = None
        if hasattr(request, 'data') and request.data is not None:
            inspection_type = request.data.get('inspection_type')

        # PSC + RightShip creation is restricted to Vessel Master only.
        if inspection_type in ('PSC', 'RS') and request.user.role != RoleCodes.VESSEL_MASTER:
            self.message = "Only Vessel Master can create PSC or RightShip inspections."
            return False

        return request.user.role in self.ALLOWED_ROLES


class CanEditInspection(permissions.BasePermission):
    """
    Permission to edit inspections.
    Per BACKEND_STRUCTURE.md:
    - VESSEL_MASTER: DRAFT only
    - OFFICE_*: any status
    """
    message = "You don't have permission to edit this inspection."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Office users can edit any status
        if request.user.user_type == 'OFFICE':
            return True

        # Vessel master can only edit DRAFT
        if request.user.role == RoleCodes.VESSEL_MASTER:
            return obj.status == 'DRAFT'

        return False


class CanDeleteInspection(permissions.BasePermission):
    """
    Permission to delete inspections.
    Per BACKEND_STRUCTURE.md: VESSEL_MASTER, status = DRAFT
    """
    message = "You can only delete draft inspections that you created."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Only DRAFT can be deleted
        if obj.status != 'DRAFT':
            self.message = "Only draft inspections can be deleted."
            return False

        # Vessel master can delete their own vessel's inspections
        if request.user.role == RoleCodes.VESSEL_MASTER:
            if request.user.user_type == 'VESSEL':
                return str(obj.vessel_id) == request.user.vessel_id
            return True

        return False


class CanSubmitInspection(permissions.BasePermission):
    """
    Permission to submit inspections.
    Per BACKEND_STRUCTURE.md: VESSEL_MASTER, OFFICE_*
    Precondition: status = DRAFT, has report
    """
    message = "You don't have permission to submit this inspection."
    ALLOWED_ROLES = [
        RoleCodes.VESSEL_MASTER,
        RoleCodes.OFFICE_PIC,
        RoleCodes.OFFICE_SSQE,
        RoleCodes.OFFICE_SUPT,
        RoleCodes.DPA,
    ]

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role not in self.ALLOWED_ROLES:
            self.message = "You don't have permission to submit this inspection."
            return False

        # Check status
        if obj.status != 'DRAFT':
            self.message = "Only draft inspections can be submitted."
            return False

        # Check vessel access for vessel users
        if request.user.user_type == 'VESSEL':
            if str(obj.vessel_id) != request.user.vessel_id:
                self.message = "You can only submit inspections for your own vessel."
                return False

        return True


class CanPICReview(permissions.BasePermission):
    """
    Permission to PIC review inspections.
    Per BACKEND_STRUCTURE.md: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
    Precondition: status = SUBMITTED
    """
    message = "You don't have permission to review this inspection."

    ALLOWED_ROLES = [
        RoleCodes.OFFICE_PIC,
        RoleCodes.OFFICE_SSQE,
        RoleCodes.OFFICE_SUPT,
    ]

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check role
        if request.user.role not in self.ALLOWED_ROLES:
            self.message = "Only PIC, SSQE, or SUPT can review inspections."
            return False

        # Check status
        if obj.status != 'SUBMITTED':
            self.message = "Only submitted inspections can be reviewed."
            return False

        return True


class CanDPAClose(permissions.BasePermission):
    """
    Permission to DPA close inspections.
    Per BACKEND_STRUCTURE.md: DPA only
    Precondition: status = PIC_REVIEWED
    """
    message = "You don't have permission to close this inspection."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check role
        if request.user.role != RoleCodes.DPA:
            self.message = "Only DPA can close inspections."
            return False

        # Check status
        if obj.status != 'PIC_REVIEWED':
            self.message = "Only PIC-reviewed inspections can be closed by DPA."
            return False

        return True


class HasVesselAccess(permissions.BasePermission):
    """
    Generic permission to check vessel access.
    - Vessel users: own vessel only
    - Global PIC/DPA office users: all vessels
    - Other office users: assigned vessels via master_RoleByVessel
    """
    message = "You don't have access to this vessel's data."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # DPA has access to all vessels
        if request.user.role == RoleCodes.DPA:
            return True

        # Get vessel_id from object
        vessel_id = getattr(obj, 'vessel_id', None)
        if not vessel_id:
            return False

        # Vessel users can only access their own vessel
        if request.user.user_type == 'VESSEL':
            return (
                str(vessel_id).strip().lower()
                == str(request.user.vessel_id).strip().lower()
            )
        # Office users - global PIC/DPA can access all; others are vessel-scoped.
        if request.user.user_type == 'OFFICE':
            from uuid import UUID as _UUID
            from core.vessel_access import (
                get_office_user_identifiers,
                get_office_user_vessel_ids,
                has_global_office_vessel_access,
            )
            user_identifiers = get_office_user_identifiers(request.user)
            if has_global_office_vessel_access(
                request.user,
                user_identifiers=user_identifiers,
            ):
                return True

            vessel_ids = get_office_user_vessel_ids(user_identifiers)
            if vessel_ids is None:
                return True
            # Normalize to UUID for safe comparison (managed vs unmanaged tables)
            try:
                vessel_uuid = _UUID(str(vessel_id))
            except (ValueError, AttributeError):
                return False
            return vessel_uuid in vessel_ids

        return False


class CanAddDeficiency(permissions.BasePermission):
    """
    Permission to add deficiencies to an inspection.
    Per BACKEND_STRUCTURE.md Section 10.4: VESSEL_MASTER, OFFICE_*
    """
    message = "You don't have permission to add deficiencies."

    ALLOWED_ROLES = [
        RoleCodes.VESSEL_MASTER,
        RoleCodes.OFFICE_PIC,
        RoleCodes.OFFICE_SSQE,
        RoleCodes.OFFICE_SUPT,
        RoleCodes.DPA,
    ]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in self.ALLOWED_ROLES


class CanUpdateDeficiencyActionCode(permissions.BasePermission):
    """
    Permission to update deficiency action code.
    Per BACKEND_STRUCTURE.md Section 10.4: VESSEL_MASTER
    """
    message = "You don't have permission to update action codes."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == RoleCodes.VESSEL_MASTER


class IsVesselMaster(permissions.BasePermission):
    """
    Permission for VESSEL_MASTER role only.
    Per BACKEND_STRUCTURE.md Section 11: PSC Follow-up registration
    """
    message = "This action requires Vessel Master role."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == RoleCodes.VESSEL_MASTER
