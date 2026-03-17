"""
Custom permission classes for PSC module.

Per BACKEND_STRUCTURE.md Section 11 (RBAC)
"""

from rest_framework import permissions

from .models import RoleCodes


class BaseRolePermission(permissions.BasePermission):
    """
    Base class for role-based permissions.

    Extracts role from JWT token claims.
    """

    def get_user_role(self, request):
        """Get user role from JWT token claims."""
        if not request.auth:
            return None
        return request.auth.get('role')

    def get_user_type(self, request):
        """Get user type (VESSEL/OFFICE) from JWT token claims."""
        if not request.auth:
            return None
        return request.auth.get('user_type')

    def get_user_vessel_id(self, request):
        """Get vessel ID for vessel users from JWT token claims."""
        if not request.auth:
            return None
        return request.auth.get('vessel_id')


class IsVesselMaster(BaseRolePermission):
    """
    Permission class for Vessel Master actions.
    """
    message = "Only Vessel Masters can perform this action."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role == RoleCodes.VESSEL_MASTER


class IsVesselUser(BaseRolePermission):
    """
    Permission class for any vessel user (Master or Crew).
    """
    message = "Only vessel users can perform this action."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.VESSEL_ROLES


class IsOfficeUser(BaseRolePermission):
    """
    Permission class for any office user.
    """
    message = "Only office users can perform this action."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.OFFICE_ROLES


class IsPICReviewer(BaseRolePermission):
    """
    Permission class for PIC review actions.

    Allows: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
    """
    message = "Only PIC reviewers can perform this action."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.PIC_REVIEWERS


class IsDPA(BaseRolePermission):
    """
    Permission class for DPA actions.
    """
    message = "Only DPA can perform this action."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role == RoleCodes.DPA


class CanCreateInspection(BaseRolePermission):
    """
    Permission for creating inspections.

    Allows: VESSEL_MASTER, all OFFICE roles
    Per BACKEND_STRUCTURE.md Section 11.1
    """
    message = "You do not have permission to create inspections."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role == RoleCodes.VESSEL_MASTER or role in RoleCodes.OFFICE_ROLES


class CanEditDraftInspection(BaseRolePermission):
    """
    Permission for editing DRAFT inspections.

    Allows: VESSEL_MASTER (DRAFT only), OFFICE_* (any status)
    Per BACKEND_STRUCTURE.md Section 11.1
    """
    message = "You do not have permission to edit this inspection."

    def has_object_permission(self, request, view, obj):
        role = self.get_user_role(request)

        # Office users can edit any status
        if role in RoleCodes.OFFICE_ROLES:
            return True

        # Vessel master can only edit DRAFT
        if role == RoleCodes.VESSEL_MASTER:
            return obj.status == 'DRAFT'

        return False


class CanSubmitInspection(BaseRolePermission):
    """
    Permission for submitting inspections.

    Allows: VESSEL_MASTER, all OFFICE roles
    """
    message = "You do not have permission to submit inspections."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role == RoleCodes.VESSEL_MASTER or role in RoleCodes.OFFICE_ROLES


class CanPICReviewInspection(BaseRolePermission):
    """
    Permission for PIC reviewing inspections.

    Allows: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
    """
    message = "Only PIC reviewers can review inspections."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.PIC_REVIEWERS


class CanDPACloseInspection(BaseRolePermission):
    """
    Permission for DPA closing inspections.

    Allows: DPA only
    """
    message = "Only DPA can close inspections."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role == RoleCodes.DPA


class CanDeleteDraftInspection(BaseRolePermission):
    """
    Permission for deleting DRAFT inspections.

    Allows: VESSEL_MASTER only
    """
    message = "Only Vessel Masters can delete draft inspections."

    def has_object_permission(self, request, view, obj):
        role = self.get_user_role(request)
        return role == RoleCodes.VESSEL_MASTER and obj.status == 'DRAFT'


class CanEditCAR(BaseRolePermission):
    """
    Permission for editing CARs.

    Allows: VESSEL_MASTER (DRAFT/REWORK only), OFFICE_* (any status)
    Per BACKEND_STRUCTURE.md Section 11.1
    """
    message = "You do not have permission to edit this CAR."

    def has_object_permission(self, request, view, obj):
        role = self.get_user_role(request)

        # Office users can edit any status
        if role in RoleCodes.OFFICE_ROLES:
            return True

        # Vessel master can only edit DRAFT or REWORK_REQUESTED
        if role == RoleCodes.VESSEL_MASTER:
            return obj.status in ['DRAFT', 'REWORK_REQUESTED']

        return False


class CanSubmitCAR(BaseRolePermission):
    """
    Permission for submitting CARs.

    Allows: VESSEL_MASTER, all OFFICE roles
    """
    message = "You do not have permission to submit CARs."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role == RoleCodes.VESSEL_MASTER or role in RoleCodes.OFFICE_ROLES


class CanPICAcceptCAR(BaseRolePermission):
    """
    Permission for PIC accepting CARs.

    Allows: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
    """
    message = "Only PIC reviewers can accept CARs."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.PIC_REVIEWERS


class CanRequestRework(BaseRolePermission):
    """
    Permission for requesting CAR rework.

    Allows: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, DPA
    """
    message = "Only office users can request rework."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.PIC_REVIEWERS or role == RoleCodes.DPA


class CanDPACloseCAR(BaseRolePermission):
    """
    Permission for DPA closing CARs.

    Allows: DPA only
    """
    message = "Only DPA can close CARs."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role == RoleCodes.DPA


class CanUploadEvidence(BaseRolePermission):
    """
    Permission for uploading evidence.

    Allows: All authenticated users
    """
    message = "You do not have permission to upload evidence."

    def has_permission(self, request, view):
        # All authenticated users can upload evidence
        return True


class CanCompleteAction(BaseRolePermission):
    """
    Permission for completing corrective actions.

    Allows:
    - Action owner (VESSEL_CREW can complete own actions)
    - VESSEL_MASTER (can complete any action)
    - OFFICE_* (can complete any action)
    """
    message = "You do not have permission to complete this action."

    def has_object_permission(self, request, view, obj):
        role = self.get_user_role(request)
        user_id = request.auth.get('user_id') if request.auth else None

        # Office users can complete any action
        if role in RoleCodes.OFFICE_ROLES:
            return True

        # Vessel master can complete any action
        if role == RoleCodes.VESSEL_MASTER:
            return True

        # Crew can only complete their own actions
        if role == RoleCodes.VESSEL_CREW:
            return (
                str(obj.owner_crew_id) == user_id or
                obj.owner_user_id == user_id
            )

        return False


class CanResolveSyncConflict(BaseRolePermission):
    """
    Permission for resolving sync conflicts.

    Allows: All OFFICE roles
    """
    message = "Only office users can resolve sync conflicts."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.OFFICE_ROLES


class CanViewAuditLog(BaseRolePermission):
    """
    Permission for viewing audit logs.

    Allows: All OFFICE roles (not vessel users)
    """
    message = "Only office users can view audit logs."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.OFFICE_ROLES


class CanCreatePhysicalVerification(BaseRolePermission):
    """
    Permission for creating physical verification.

    Allows: OFFICE_*, DPA
    """
    message = "Only office users can create physical verification."

    def has_permission(self, request, view):
        role = self.get_user_role(request)
        return role in RoleCodes.OFFICE_ROLES


class CanClosePhysicalVerification(BaseRolePermission):
    """
    Permission for closing physical verification.

    Allows: Assigned verifier or DPA
    """
    message = "Only the assigned verifier or DPA can close physical verification."

    def has_object_permission(self, request, view, obj):
        role = self.get_user_role(request)
        user_id = request.auth.get('user_id') if request.auth else None
        employee_id = request.auth.get('employee_id') if request.auth else None

        # DPA can always close
        if role == RoleCodes.DPA:
            return True

        # Assigned verifier can close
        if obj.verifier_user_id == employee_id:
            return True

        if str(obj.verifier_crew_id) == user_id:
            return True

        return False
