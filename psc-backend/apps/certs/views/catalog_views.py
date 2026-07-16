from __future__ import annotations

from typing import Any
import uuid

from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import HasCatalogReadPermission, IsCatalogBulkActionWriter, IsCatalogHardPurgeWriter, IsCatalogWriter
from apps.certs.serializers.catalog import (
    CatalogRowWriteSerializer,
    SHIP_TYPE_SET,
    serialize_catalog_audit_event,
    serialize_catalog_row,
    serialize_catalog_section,
)
from apps.certs.services.audit_log import record_audit_event, resolve_actor_id
from apps.certs.services.catalog_repository import CatalogRepository


repository = CatalogRepository()


class CatalogReadPermissionMixin:
    permission_classes = [IsAuthenticated, HasCatalogReadPermission]


class CatalogWritePermissionMixin:
    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), HasCatalogReadPermission()]
        return [IsAuthenticated(), IsCatalogWriter()]


class CatalogSectionListView(CatalogReadPermissionMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        sections = [serialize_catalog_section(row) for row in repository.list_sections()]
        return Response({"results": sections})


class CatalogRowListCreateView(CatalogWritePermissionMixin, generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        section_id = request.query_params.get("sectionId")
        is_active = request.query_params.get("isActive")
        page_number = _parse_positive_int(request.query_params.get("page"), default=None, maximum=None)
        page_size = _parse_positive_int(request.query_params.get("pageSize"), default=None, maximum=100)
        applicable_ship_type = request.query_params.get("applicableShipType") or None
        if applicable_ship_type:
            applicable_ship_type = applicable_ship_type.strip().lower()
            if applicable_ship_type not in SHIP_TYPE_SET or applicable_ship_type == "all":
                return Response(
                    {"applicableShipType": "Filter must be one of the specific ship types."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        page = repository.list_rows(
            section_id=int(section_id) if section_id else None,
            is_active=_parse_bool(is_active) if is_active not in (None, "") else None,
            q=request.query_params.get("q") or None,
            applicable_ship_type=applicable_ship_type,
            page=page_number,
            page_size=page_size,
        )
        return Response(
            {
                "count": page.count,
                "page": page.page,
                "pageSize": page.page_size,
                "results": [serialize_catalog_row(row) for row in page.results],
            }
        )

    def post(self, request, *args, **kwargs):
        serializer = CatalogRowWriteSerializer(data=request.data, context={"is_create": True})
        serializer.is_valid(raise_exception=True)
        metadata, metadata_error = _catalog_create_metadata(request)
        if metadata_error:
            return metadata_error
        parent_error = _validate_parent_choice(serializer.validated_data)
        if parent_error:
            return parent_error
        reason = serializer.validated_data.pop("reason", None)
        row = repository.create_row(serializer.validated_data, actor_id=resolve_actor_id(request.user))
        serialized = serialize_catalog_row(row)
        record_audit_event(
            actor=request.user,
            action="create_catalog_row",
            entity_type="catalog_row",
            entity_id=serialized["id"],
            before=None,
            after=serialized,
            reason=reason or "Catalog row created.",
            metadata=metadata,
        )
        return Response(serialized, status=status.HTTP_201_CREATED)


class CatalogRowDetailView(CatalogWritePermissionMixin, generics.GenericAPIView):
    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), HasCatalogReadPermission()]
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsCatalogHardPurgeWriter()]
        return [IsAuthenticated(), IsCatalogWriter()]

    def get(self, request, catalog_id: str, *args, **kwargs):
        row = _resolve_catalog_row(catalog_id)
        if row is None:
            return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_catalog_row(row))

    def patch(self, request, catalog_id: str, *args, **kwargs):
        current_row = _resolve_catalog_row(catalog_id)
        if current_row is None:
            return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_catalog_id = _catalog_id_from_row(current_row, catalog_id)
        serializer = CatalogRowWriteSerializer(
            data=request.data,
            partial=True,
            context={"current_row": current_row},
        )
        serializer.is_valid(raise_exception=True)
        parent_error = _validate_parent_choice(serializer.validated_data, current_catalog_id=resolved_catalog_id)
        if parent_error:
            return parent_error
        dynamic_error = _validate_dynamic_children_choice(serializer.validated_data, current_catalog_id=resolved_catalog_id)
        if dynamic_error:
            return dynamic_error
        reason = serializer.validated_data.pop("reason", None)
        before, after = repository.update_row(
            resolved_catalog_id,
            serializer.validated_data,
            actor_id=resolve_actor_id(request.user),
        )
        if after is None:
            return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)
        serialized_before = serialize_catalog_row(before) if before else None
        serialized_after = serialize_catalog_row(after)
        record_audit_event(
            actor=request.user,
            action="update_catalog_row",
            entity_type="catalog_row",
            entity_id=serialized_after["id"],
            before=serialized_before,
            after=serialized_after,
            reason=reason or "Catalog row updated.",
            metadata={"source": "api.certs.catalog.rows"},
        )
        return Response(serialized_after)

    def delete(self, request, catalog_id: str, *args, **kwargs):
        return _hard_purge_catalog_row(request, str(catalog_id))


class CatalogRowDeprecateView(CatalogWritePermissionMixin, generics.GenericAPIView):
    def post(self, request, catalog_id: str, *args, **kwargs):
        reason = str(request.data.get("reason") or "").strip()
        if not reason:
            return Response({"reason": "Deprecation reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        current_row = _resolve_catalog_row(catalog_id)
        if current_row is None:
            return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)
        resolved_catalog_id = _catalog_id_from_row(current_row, catalog_id)

        before, after = repository.update_row(
            resolved_catalog_id,
            {"isActive": False},
            actor_id=resolve_actor_id(request.user),
        )
        if after is None:
            return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)

        serialized_before = serialize_catalog_row(before) if before else None
        serialized_after = serialize_catalog_row(after)
        record_audit_event(
            actor=request.user,
            action="deprecate_catalog_row",
            entity_type="catalog_row",
            entity_id=serialized_after["id"],
            before=serialized_before,
            after=serialized_after,
            reason=reason,
            metadata={"source": "api.certs.catalog.rows.deprecate"},
        )
        return Response(serialized_after)


class CatalogRowBulkSoftDeleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsCatalogBulkActionWriter]

    def post(self, request, *args, **kwargs):
        catalog_ids, ids_error = _catalog_id_list(request.data.get("catalogIds"))
        if ids_error:
            return ids_error
        reason, reason_error = _required_reason(request.data.get("reason"))
        if reason_error:
            return reason_error

        actor_id = resolve_actor_id(request.user)
        with transaction.atomic():
            changed_rows = repository.bulk_soft_delete_rows(catalog_ids, actor_id=actor_id)
            serialized_pairs = [
                (serialize_catalog_row(before), serialize_catalog_row(after))
                for before, after in changed_rows
            ]
            metadata = {
                "source": "api.certs.catalog.rows.bulk_soft_delete",
                "batchSize": len(catalog_ids),
                "catalogIds": catalog_ids,
            }
            for before, after in serialized_pairs:
                record_audit_event(
                    actor=request.user,
                    action="bulk_soft_delete",
                    entity_type="catalog_row",
                    entity_id=after["id"],
                    before=before,
                    after=after,
                    reason=reason,
                    metadata=metadata,
                )

        return Response(
            {
                "requestedCount": len(catalog_ids),
                "updatedCount": len(serialized_pairs),
                "results": [after for _, after in serialized_pairs],
            }
        )


class CatalogRowHardPurgeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsCatalogHardPurgeWriter]

    def delete(self, request, catalog_id: str, *args, **kwargs):
        return _hard_purge_catalog_row(request, str(catalog_id))


class CatalogRowAuditHistoryView(CatalogReadPermissionMixin, generics.GenericAPIView):
    def get(self, request, catalog_id: str, *args, **kwargs):
        row = _resolve_catalog_row(catalog_id)
        if row is None:
            return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)
        events = repository.list_catalog_audit_events(_catalog_id_from_row(row, catalog_id))
        return Response({"results": [serialize_catalog_audit_event(event) for event in events]})


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _parse_positive_int(value: str | None, *, default: int | None, maximum: int | None) -> int | None:
    if value in (None, ""):
        return default
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default
    parsed = max(1, parsed)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def _hard_purge_catalog_row(request, catalog_id: str) -> Response:
    reason, reason_error = _required_reason(request.data.get("reason"))
    if reason_error:
        return reason_error

    try:
        with transaction.atomic():
            row = _resolve_catalog_row(catalog_id)
            if row is None:
                return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)
            before = repository.delete_row(_catalog_id_from_row(row, catalog_id))
            if before is None:
                return Response({"detail": "Catalog row not found."}, status=status.HTTP_404_NOT_FOUND)
            serialized_before = serialize_catalog_row(before)
            record_audit_event(
                actor=request.user,
                action="hard_purge_catalog_row",
                entity_type="catalog_row",
                entity_id=serialized_before["id"],
                before=serialized_before,
                after=None,
                reason=reason,
                metadata={"source": "api.certs.catalog.rows.hard_purge"},
            )
    except IntegrityError:
        return Response(
            {
                "detail": (
                    "Catalog row is still referenced by retained Certs data. "
                    "Hard purge is blocked until dependent rows are cleared by their retention path."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)


def _resolve_catalog_row(identifier: str) -> dict[str, Any] | None:
    value = str(identifier).strip()
    row = repository.get_row(value)
    if row is not None:
        return row
    return repository.get_row_by_code(value)


def _catalog_id_from_row(row: dict[str, Any], fallback: str) -> str:
    try:
        return str(uuid.UUID(str(fallback)))
    except (TypeError, ValueError, AttributeError):
        pass
    return str(row["catalog_id"]) if isinstance(row, dict) and row.get("catalog_id") else str(fallback)


def _required_reason(value: object) -> tuple[str, Response | None]:
    reason = str(value or "").strip()
    if not reason:
        return "", Response({"reason": "Reason is required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(reason) < 10:
        return "", Response({"reason": "Reason must be at least 10 characters."}, status=status.HTTP_400_BAD_REQUEST)
    return reason, None


def _catalog_id_list(value: object) -> tuple[list[str], Response | None]:
    if not isinstance(value, list):
        return [], Response({"catalogIds": "Catalog IDs must be supplied as a list."}, status=status.HTTP_400_BAD_REQUEST)
    if not value:
        return [], Response({"catalogIds": "At least one catalog row is required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(value) > 50:
        return [], Response({"catalogIds": "Bulk soft-delete is capped at 50 rows per batch."}, status=status.HTTP_400_BAD_REQUEST)

    catalog_ids: list[str] = []
    seen: set[str] = set()
    for item in value:
        try:
            catalog_id = str(uuid.UUID(str(item)))
        except (TypeError, ValueError, AttributeError):
            return [], Response({"catalogIds": "Every catalog ID must be a valid UUID."}, status=status.HTTP_400_BAD_REQUEST)
        if catalog_id not in seen:
            catalog_ids.append(catalog_id)
            seen.add(catalog_id)
    return catalog_ids, None


def _catalog_create_metadata(request) -> tuple[dict[str, Any], Response | None]:
    source = (request.query_params.get("source") or "").strip()
    if source != "onboarding_gap_fill":
        return {"source": "api.certs.catalog.rows"}, None

    vessel_id = (request.query_params.get("vesselId") or "").strip()
    if not vessel_id:
        return {}, Response(
            {"vesselId": "Vessel ID is required for onboarding inline catalog promotion."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    metadata = {
        "source": "api.certs.catalog.inline_promotion",
        "promotionSource": "onboarding_gap_fill",
        "vesselId": vessel_id,
    }
    batch_id = (request.query_params.get("batchId") or "").strip()
    if batch_id:
        metadata["batchId"] = batch_id
    return metadata, None


def _validate_parent_choice(values: dict[str, Any], *, current_catalog_id: str | None = None) -> Response | None:
    if "parentId" not in values:
        return None
    parent_id = values.get("parentId")
    if parent_id in (None, ""):
        return None

    parent_id_text = str(parent_id)
    if current_catalog_id and parent_id_text.lower() == str(current_catalog_id).lower():
        return Response(
            {"parentId": "A catalog row cannot be its own parent."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    parent_row = repository.get_row(parent_id_text)
    if parent_row is None:
        return Response(
            {"parentId": "Parent catalog row was not found."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if parent_row.get("parent_id"):
        return Response(
            {"parentId": "Catalog Admin supports only one child level in V1."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if values.get("parentSupportsDynamicChildren"):
        return Response(
            {"parentSupportsDynamicChildren": "Only top-level catalog parent rows can support dynamic child TrackedItems."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if current_catalog_id:
        current_row = repository.get_row(str(current_catalog_id))
        if current_row and current_row.get("parent_supports_dynamic_children"):
            return Response(
                {"parentSupportsDynamicChildren": "Only top-level catalog parent rows can support dynamic child TrackedItems."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    if current_catalog_id and repository.has_children(str(current_catalog_id)):
        return Response(
            {"parentId": "Rows that already have children cannot be moved under a parent in V1."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


def _validate_dynamic_children_choice(values: dict[str, Any], *, current_catalog_id: str) -> Response | None:
    if not values.get("parentSupportsDynamicChildren"):
        return None
    current_row = repository.get_row(str(current_catalog_id))
    if current_row and current_row.get("parent_id"):
        return Response(
            {"parentSupportsDynamicChildren": "Only top-level catalog parent rows can support dynamic child TrackedItems."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None
