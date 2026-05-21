from __future__ import annotations

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.vessel_scope import get_scoped_vessel_ids, has_global_vessel_scope, user_has_vessel_access
from apps.safety.models import SCMMeeting
from apps.safety.public_id import get_by_public_id_or_pk
from apps.safety.services.closed_since_last_scm import ClosedSinceLastSCMService
from apps.safety.views.scm import SCMViewMixin, _normalized_role


GLOBAL_ROLES = {"DPA", "FM", "FLEET MANAGER"}


class SCMClosedSinceLastMixin(SCMViewMixin):
    service_class = ClosedSinceLastSCMService

    @staticmethod
    def _normalize_vessel_id(value: object) -> str:
        return str(value or "").strip()

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_service(self) -> ClosedSinceLastSCMService:
        return self.service_class()

    def _resolve_vessel_id(self) -> str:
        requested = self.request.query_params.get("vessel_id")
        if requested not in (None, ""):
            return self._normalize_vessel_id(requested)

        vessel_ids = sorted(get_scoped_vessel_ids(self.request.user))
        if vessel_ids:
            return self._normalize_vessel_id(vessel_ids[0])

        direct_vessel_id = getattr(self.request.user, "vessel_id", None)
        if direct_vessel_id not in (None, ""):
            return self._normalize_vessel_id(direct_vessel_id)

        raise ValidationError({"vessel_id": "vessel_id is required when the user has no scoped vessel list."})

    def _ensure_vessel_access(self, vessel_id: str) -> None:
        user = getattr(self.request, "user", None)
        if user is None:
            raise PermissionDenied("Authentication required.")

        if has_global_vessel_scope(user) or _normalized_role(user) in GLOBAL_ROLES:
            return

        scoped_vessel_ids = get_scoped_vessel_ids(user)
        if not scoped_vessel_ids:
            raise PermissionDenied("No vessel scope available for this user.")

        normalized_vessel_id = self._normalize_vessel_id(vessel_id)
        normalized_scope_ids = {
            self._normalize_vessel_id(scoped_vessel_id) for scoped_vessel_id in scoped_vessel_ids
        }
        if not normalized_vessel_id:
            raise ValidationError({"vessel_id": "vessel_id is required."})

        if normalized_vessel_id not in normalized_scope_ids or not user_has_vessel_access(user, normalized_vessel_id):
            raise PermissionDenied("Requested vessel is outside the user's Safety scope.")


class SCMClosedSinceLastMeetingView(SCMClosedSinceLastMixin, generics.GenericAPIView):
    def get_meeting(self) -> SCMMeeting:
        queryset = self._apply_filters(SCMMeeting.objects.filter(is_deleted=False))
        return get_by_public_id_or_pk(queryset, self.kwargs["id"])

    def get(self, request, *args, **kwargs):
        payload = self.get_service().fetch_for_meeting(self.get_meeting())
        return Response(payload)


class SCMClosedSinceLastVesselView(SCMClosedSinceLastMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        vessel_id = self._resolve_vessel_id()
        self._ensure_vessel_access(vessel_id)
        payload = self.get_service().fetch_for_vessel(vessel_id)
        return Response(payload)
