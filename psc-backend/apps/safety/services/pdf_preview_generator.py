from __future__ import annotations

from apps.safety.models import Incident


class PdfPreviewGenerator:
    def build_preview(self, incident: Incident) -> dict[str, object]:
        available = incident.record_type == Incident.RecordType.INCIDENT
        return {
            "available": available,
            "status": "READY_TO_GENERATE" if available else "NOT_AVAILABLE",
            "incident_id": incident.pk,
            "expected_sections": 10,
            "download_path": f"/api/safety/incidents/{incident.public_id}/pdf/",
            "message": (
                "Formal incident PDF generation is available from the Step 6.1 renderer."
                if available
                else "Formal incident PDF generation only applies to incident records."
            ),
        }
