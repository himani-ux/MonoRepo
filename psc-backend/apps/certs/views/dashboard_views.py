from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import (
    PRINT_EXPORT_FORM_ID,
    TRACKED_ITEM_FORM_ID,
    HasTrackedItemReadPermission,
    HasAnyCertsFormPermission,
    has_request_certs_perm,
    normalized_role,
    user_can_access_vessel,
)
from apps.certs.services.vessel_dashboard import (
    FleetDashboardRepository,
    VesselDashboardRepository,
    serialize_vessel_dashboard,
)


repository = VesselDashboardRepository()
fleet_repository = FleetDashboardRepository()
FLEET_MANAGER_ROLES = {"FM", "FLEET MANAGER"}
DPA_ROLES = {"DPA", "SEQ MANAGER", "ADMIN", "SUPER ADMIN", "SYSTEM ADMIN"}


class VesselDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasTrackedItemReadPermission]

    def get(self, request, imo: str, *args, **kwargs):
        dashboard = repository.get_dashboard(str(imo))
        if dashboard is None:
            return Response({"detail": "Vessel not found."}, status=status.HTTP_404_NOT_FOUND)
        vessel_id = str(dashboard.vessel.get("vessel_id") or "")
        if not user_can_access_vessel(request.user, vessel_id):
            return Response({"detail": "You do not have access to this vessel."}, status=status.HTTP_403_FORBIDDEN)
        return Response(serialize_vessel_dashboard(dashboard))


class FleetDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasAnyCertsFormPermission]

    def get(self, request, *args, **kwargs):
        role = normalized_role(request.user)
        payload = {}
        if has_request_certs_perm(request, TRACKED_ITEM_FORM_ID):
            payload["onboardedVessels"] = [
                vessel
                for vessel in fleet_repository.list_onboarded_vessels()
                if user_can_access_vessel(request.user, str(vessel.get("id") or ""))
            ]
        if role in FLEET_MANAGER_ROLES:
            if not has_request_certs_perm(request, PRINT_EXPORT_FORM_ID):
                return Response({"detail": "You do not have access to print governance signals."}, status=status.HTTP_403_FORBIDDEN)
            payload["highVolumePrintActivity"] = fleet_repository.get_high_volume_print_activity()
        if role in DPA_ROLES:
            payload["cadenceHeartbeat"] = fleet_repository.get_cadence_heartbeat()
            payload["bouncingEmailDelivery"] = fleet_repository.get_bouncing_email_delivery()
        if not payload:
            return Response({"detail": "You do not have access to the Certs fleet dashboard."}, status=status.HTTP_403_FORBIDDEN)
        return Response(payload)
