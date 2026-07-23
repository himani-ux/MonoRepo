from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.mail import EmailMessage, get_connection
from django.utils.text import get_valid_filename

from apps.certs.services.pdf_blob_repository import PdfBlobRepository
from apps.certs.services.pdf_blob_storage import resolve_pdf_blob_path


@dataclass(frozen=True)
class PrintArtifactFile:
    kind: str
    absolute_path: Path
    filename: str
    content_type: str


class PrintArtifactDeliveryError(RuntimeError):
    pass


ARTIFACT_FILE_SPECS = {
    "pdf": {
        "blob_field": "pdf_blob_id",
        "content_type": "application/pdf",
        "fallback_suffix": "pdf",
    },
    "excel": {
        "blob_field": "excel_blob_id",
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "fallback_suffix": "xlsx",
    },
    "zip": {
        "blob_field": "bundle_zip_blob_id",
        "content_type": "application/zip",
        "fallback_suffix": "zip",
    },
}


class PrintArtifactDeliveryService:
    def __init__(
        self,
        *,
        blob_repository: PdfBlobRepository | None = None,
        resolve_blob_path: Callable[[dict[str, Any]], Path] = resolve_pdf_blob_path,
        email_connection_factory: Callable[..., object] = get_connection,
    ) -> None:
        self.blob_repository = blob_repository or PdfBlobRepository()
        self.resolve_blob_path = resolve_blob_path
        self.email_connection_factory = email_connection_factory

    def get_download_file(self, artifact: dict[str, Any], kind: str) -> PrintArtifactFile:
        normalized_kind = str(kind or "").strip().lower()
        spec = ARTIFACT_FILE_SPECS.get(normalized_kind)
        if spec is None:
            raise PrintArtifactDeliveryError("Requested file type is not available.")

        blob_id = artifact.get(str(spec["blob_field"]))
        if not blob_id:
            raise PrintArtifactDeliveryError("Requested file was not generated for this artifact.")

        blob = self.blob_repository.get_blob(str(blob_id))
        if blob is None:
            raise PrintArtifactDeliveryError("Requested file record was not found.")

        absolute_path = self.resolve_blob_path(blob)
        if not absolute_path.is_file():
            raise PrintArtifactDeliveryError("Requested file is missing from storage.")

        filename = get_valid_filename(str(blob.get("filename") or "").strip())
        if not filename:
            filename = f"{artifact.get('print_id') or 'certs-artifact'}.{spec['fallback_suffix']}"

        content_type = str(spec["content_type"])
        if filename.lower().endswith(".csv"):
            content_type = "text/csv"

        return PrintArtifactFile(
            kind=normalized_kind,
            absolute_path=absolute_path,
            filename=filename,
            content_type=content_type,
        )

    def send_artifact_email(self, artifact: dict[str, Any], *, recipient_email: str | None = None) -> dict[str, Any]:
        recipient = str(recipient_email or artifact.get("recipient_email") or "").strip()
        if not recipient:
            return {
                "status": "not_requested",
                "message": "",
                "recipient": "",
                "attachmentKinds": [],
            }

        try:
            attachments = self._email_attachments_for_artifact(artifact)
        except (PrintArtifactDeliveryError, SuspiciousFileOperation) as exc:
            return {
                "status": "failed",
                "message": str(exc),
                "recipient": recipient,
                "attachmentKinds": [],
            }

        print_id = str(artifact.get("print_id") or "")
        is_share_bundle = str(artifact.get("scope") or "").strip().lower() == "share_bundle"
        subject = (
            f"VIMS certificate share bundle {print_id}"
            if is_share_bundle
            else f"VIMS certificate export {print_id}"
        ).strip()
        body = "\n".join(
            [
                "Dear recipient,",
                "",
                "Please find the generated VIMS certificate file attached.",
                f"Reference: {print_id}",
                "",
                "Regards,",
                "KSM Marine",
            ]
        )
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[recipient],
        )
        for attachment in attachments:
            message.attach(
                attachment.filename,
                attachment.absolute_path.read_bytes(),
                attachment.content_type,
            )

        try:
            with self.email_connection_factory(timeout=getattr(settings, "EMAIL_TIMEOUT", 15)) as email_connection:
                sent_count = email_connection.send_messages([message]) or 0
        except Exception as exc:
            raise PrintArtifactDeliveryError(
                "Email could not be sent. Check the backend SMTP settings used by Circular emails."
            ) from exc

        if sent_count < 1:
            return {
                "status": "failed",
                "message": "Email was prepared but the mail server did not accept it.",
                "recipient": recipient,
                "attachmentKinds": [attachment.kind for attachment in attachments],
            }

        return {
            "status": "sent",
            "message": f"Email sent to {recipient}.",
            "recipient": recipient,
            "attachmentKinds": [attachment.kind for attachment in attachments],
        }

    def _email_attachments_for_artifact(self, artifact: dict[str, Any]) -> list[PrintArtifactFile]:
        if str(artifact.get("scope") or "").strip().lower() == "share_bundle":
            return [self.get_download_file(artifact, "zip")]

        attachments: list[PrintArtifactFile] = []
        for kind in ("pdf", "excel"):
            try:
                attachments.append(self.get_download_file(artifact, kind))
            except PrintArtifactDeliveryError:
                continue
        if not attachments:
            raise PrintArtifactDeliveryError("No generated files are available to email.")
        return attachments
