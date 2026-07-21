from __future__ import annotations

from typing import Any

from apps.certs.services.snapshot_repository import ClassSnapshotRepository


def run_class_snapshot_parser(
    snapshot_id: str,
    *,
    repository: ClassSnapshotRepository | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Run the class snapshot parser/reconciliation worker for one snapshot."""
    return (repository or ClassSnapshotRepository()).reparse_snapshot(str(snapshot_id))
