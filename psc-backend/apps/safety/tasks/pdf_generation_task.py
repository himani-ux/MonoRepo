from __future__ import annotations

from apps.safety.services.pdf_renderer import IncidentPdfRenderResult, IncidentPdfRenderer


def generate_incident_pdf_export(*, incident_id: int, viewer_user) -> IncidentPdfRenderResult:
    return IncidentPdfRenderer().render_incident_pdf(
        incident_id=incident_id,
        viewer_user=viewer_user,
        persist=True,
    )
