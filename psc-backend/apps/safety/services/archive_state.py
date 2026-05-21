from __future__ import annotations

from django.db.models import Q


def archive_filter(*, archived: bool) -> Q:
    if archived:
        return Q(is_archived=True, archived_at__isnull=False)
    return Q(is_archived=False, archived_at__isnull=True)


def is_archived_record(record) -> bool:
    return bool(getattr(record, "is_archived", False))
