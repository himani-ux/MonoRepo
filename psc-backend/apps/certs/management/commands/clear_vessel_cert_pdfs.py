from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.certs.services.pdf_blob_storage import delete_stored_blob


@dataclass(frozen=True)
class BlobRow:
    blob_id: str
    tracked_item_id: str
    storage_path: str
    filename: str


class Command(BaseCommand):
    help = "Clear all uploaded Certs PDFs for one vessel. Dry-run by default."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--vessel-id", help="VesselData.id UUID.")
        parser.add_argument("--imo", help="VesselData.imoNumber.")
        parser.add_argument("--name", help="Exact VesselData.vesselName.")
        parser.add_argument("--reason", required=True, help="Reason for audit/operator trace.")
        parser.add_argument("--actor-id", default="system.clear_vessel_cert_pdfs", help="updated_by value.")
        parser.add_argument("--apply", action="store_true", help="Apply the cleanup. Without this, only prints counts.")

    def handle(self, *args, **options):
        selector = {
            "vessel_id": options.get("vessel_id"),
            "imo": options.get("imo"),
            "name": options.get("name"),
        }
        if sum(1 for value in selector.values() if value) != 1:
            raise CommandError("Provide exactly one of --vessel-id, --imo, or --name.")

        vessel = _resolve_vessel(selector)
        if vessel is None:
            raise CommandError("No matching vessel found.")

        vessel_id = str(vessel["id"])
        blobs = _list_vessel_cert_blobs(vessel_id)
        tracked_item_ids = sorted({blob.tracked_item_id for blob in blobs})

        mode = "applied" if options["apply"] else "dry_run"
        self.stdout.write(
            self.style.WARNING(
                f"clear_vessel_cert_pdfs {mode} vessel={vessel['vesselName']} "
                f"imo={vessel.get('imoNumber') or 'n/a'} tracked_items={len(tracked_item_ids)} blobs={len(blobs)}"
            )
        )
        if not options["apply"] or not blobs:
            for blob in blobs[:20]:
                self.stdout.write(f"{blob.tracked_item_id} {blob.blob_id} {blob.filename}")
            if len(blobs) > 20:
                self.stdout.write(f"... {len(blobs) - 20} more blob(s)")
            return

        reason = str(options["reason"]).strip()
        actor_id = str(options["actor_id"]).strip() or "system.clear_vessel_cert_pdfs"
        with transaction.atomic():
            _reset_tracked_items_for_pdf_cleanup(tracked_item_ids, actor_id=actor_id)
            _delete_pdf_blob_rows([blob.blob_id for blob in blobs])

        deleted_files = 0
        missing_files = 0
        for blob in blobs:
            try:
                if delete_stored_blob(blob.storage_path):
                    deleted_files += 1
                else:
                    missing_files += 1
            except Exception as exc:
                self.stderr.write(f"Could not delete stored file for blob {blob.blob_id}: {exc}")

        self.stdout.write(
            self.style.SUCCESS(
                f"clear_vessel_cert_pdfs applied tracked_items={len(tracked_item_ids)} "
                f"deleted_blob_rows={len(blobs)} deleted_files={deleted_files} missing_files={missing_files} "
                f"reason={reason}"
            )
        )


def _resolve_vessel(selector: dict[str, str | None]) -> dict | None:
    clauses: list[str] = []
    params: list[str] = []
    if selector.get("vessel_id"):
        clauses.append("id = CAST(%s AS uniqueidentifier)")
        params.append(str(selector["vessel_id"]))
    if selector.get("imo"):
        clauses.append("imoNumber = %s")
        params.append(str(selector["imo"]))
    if selector.get("name"):
        clauses.append("vesselName = %s")
        params.append(str(selector["name"]))

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT TOP 2 id, vesselName, imoNumber, vesselCode
            FROM dbo.VesselData
            WHERE {' OR '.join(clauses)}
            """,
            params,
        )
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    if len(rows) > 1:
        raise CommandError("Vessel selector matched more than one row.")
    return rows[0] if rows else None


def _list_vessel_cert_blobs(vessel_id: str) -> list[BlobRow]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.blob_id, p.tracked_item_id, p.blob_storage_path, p.filename
            FROM dbo.vims_certs_pdf_blob p
            INNER JOIN dbo.vims_certs_tracked_item t ON t.tracked_item_id = p.tracked_item_id
            WHERE t.vessel_id = CAST(%s AS uniqueidentifier)
            ORDER BY p.uploaded_at DESC
            """,
            [vessel_id],
        )
        return [
            BlobRow(
                blob_id=str(row[0]),
                tracked_item_id=str(row[1]),
                storage_path=str(row[2] or ""),
                filename=str(row[3] or ""),
            )
            for row in cursor.fetchall()
        ]


def _reset_tracked_items_for_pdf_cleanup(tracked_item_ids: list[str], *, actor_id: str) -> None:
    if not tracked_item_ids:
        return
    placeholders = ", ".join(["CAST(%s AS uniqueidentifier)"] * len(tracked_item_ids))
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE t
            SET t.pdf_attachment_id = NULL,
                t.pdf_missing = 1,
                t.status = 'pending_first_upload',
                t.certificate_number = NULL,
                t.place_of_issue = NULL,
                t.issue_date = NULL,
                t.expiry_date = NULL,
                t.issuing_authority = COALESCE(NULLIF(c.issuing_authority_type, ''), 'Company'),
                t.version = t.version + 1,
                t.updated_at = SYSUTCDATETIME(),
                t.updated_by = %s
            FROM dbo.vims_certs_tracked_item t
            INNER JOIN dbo.vims_certs_catalog_row c ON c.catalog_id = t.catalog_id
            WHERE t.tracked_item_id IN ({placeholders})
            """,
            [actor_id, *tracked_item_ids],
        )


def _delete_pdf_blob_rows(blob_ids: list[str]) -> None:
    if not blob_ids:
        return
    placeholders = ", ".join(["CAST(%s AS uniqueidentifier)"] * len(blob_ids))
    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM dbo.vims_certs_pdf_blob WHERE blob_id IN ({placeholders})",
            blob_ids,
        )
