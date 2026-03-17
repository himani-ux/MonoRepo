"""
Sync permission classes per BACKEND_STRUCTURE.md Section 11 (RBAC).

Permission matrix for sync operations:
- Pull/Push: VESSEL_MASTER, VESSEL_CREW
- Resolve Conflict: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, DPA

Implements: FEAT-SYNC-002, FEAT-SYNC-003, FEAT-SYNC-005
"""

from rest_framework import permissions

from apps.accounts.models import RoleCodes


class IsVesselUser(permissions.BasePermission):
    """
    Allow only vessel users (Master or Crew) to perform sync pull/push.

    Per BACKEND_STRUCTURE.md Section 10.9:
    - POST /api/psc/sync/pull/ — Roles: VESSEL_MASTER, VESSEL_CREW
    - POST /api/psc/sync/push/ — Roles: VESSEL_MASTER, VESSEL_CREW
    """
    message = "Only vessel users can perform sync operations."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in RoleCodes.VESSEL_ROLES


class CanResolveConflict(permissions.BasePermission):
    """
    Allow only Office/DPA users to resolve sync conflicts.

    Per BACKEND_STRUCTURE.md Section 11.1 RBAC matrix:
    - Resolve Sync Conflict: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, DPA
    Per PRD.md FEAT-SYNC-005: "Only Office/DPA can resolve"
    """
    message = "Only office users can resolve sync conflicts."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in [
            RoleCodes.OFFICE_PIC,
            RoleCodes.OFFICE_SSQE,
            RoleCodes.OFFICE_SUPT,
            RoleCodes.DPA,
        ]
