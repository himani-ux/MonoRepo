from __future__ import annotations

from apps.safety.models import Incident


class PdfPreviewGenerator:
    def build_preview(self, incident: Incident) -> dict[str, object]:
        is_incident = incident.record_type == Incident.RecordType.INCIDENT
        exportable = is_incident
        payload: dict[str, object] = {
            "available": exportable,
            "status": "READY_TO_GENERATE" if exportable else "NOT_AVAILABLE",
            "incident_id": incident.pk,
            "expected_sections": 10,
            "message": (
                "Formal incident PDF generation is available."
                if exportable
                else "Formal incident PDF generation only applies to incident records."
            ),
        }
        if exportable:
            payload["download_path"] = f"/api/safety/incidents/{incident.id}/pdf/"
        return payload
