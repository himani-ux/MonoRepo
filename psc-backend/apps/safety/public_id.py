from __future__ import annotations

import uuid

from django.shortcuts import get_object_or_404


def is_uuid_identifier(value: object) -> bool:
    if isinstance(value, uuid.UUID):
        return True
    try:
        uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return False
    return True


def get_by_public_id_or_pk(queryset, identifier):
    lookup_value = str(identifier).strip()
    if is_uuid_identifier(lookup_value):
        return get_object_or_404(queryset, public_id=lookup_value)
    return get_object_or_404(queryset, pk=lookup_value)


def resolve_public_or_pk_filter(identifier: object) -> dict[str, object]:
    lookup_value = str(identifier).strip()
    if is_uuid_identifier(lookup_value):
        return {"public_id": lookup_value}
    return {"pk": lookup_value}
